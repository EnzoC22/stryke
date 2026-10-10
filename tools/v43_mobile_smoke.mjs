import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const base = process.env.STRYKE_TEST_URL || 'http://127.0.0.1:8765/';
const browser = await chromium.launch({
  headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--disable-dev-shm-usage']
});

function withHooks(html) {
  const needle = /<\/script>\s*<\/body>/i;
  if (!needle.test(html)) throw Error('Could not find final inline module');
  const hooks = `
  // Test-only: injected into the served HTML by Playwright, never committed to game.
  window.__strykeMobileSmoke = {
    isMobile: () => MOBILE,
    prepare: () => {
      inGame = true;
      me.alive = true;
      C.st = { ...(C.st || {}), mode: 'rounds' };
      C.buyOpen = false;
      C.eTip = true;
      ZC.on = false;
      $('#pause')?.classList.add('hidden');
      $('#menu')?.classList.add('hidden');
      $('#hud')?.classList.remove('hidden');
      $('#click')?.classList.add('hidden');
      mobileGameOn();
      return true;
    },
    setZombie: (enabled) => {
      ZC.on = enabled;
      ZC.act = null;
      keys.KeyE = false;
      keys.KeyF = false;
    },
    state: () => ({
      game: inGame,
      mobile: MOBILE,
      e: Boolean(keys.KeyE),
      f: Boolean(keys.KeyF),
      buy: Boolean(C.buyOpen),
      paused: !$('#pause').classList.contains('hidden'),
      controlsVisible: !$('#mobileControls').classList.contains('hidden')
    }),
    forceEnd: () => mobileUseEnd()
  };
`;
  return html.replace(needle, hooks + '\n$&');
}

async function boot(page, label) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message.slice(0, 350)));
  page.on('console', message => {
    if (message.type() === 'error') console.log(label, 'console error:', message.text().slice(0, 200));
  });
  page.on('response', response => {
    if (response.status() === 404) console.log(label, 'missing resource:', response.url());
  });
  const response = await page.goto(base, {waitUntil: 'domcontentloaded', timeout: 60000});
  assert.equal(response.status(), 200, label + ' HTML returned non-200 status');
  await page.locator('#menu').waitFor({state: 'visible', timeout: 45000});
  await page.locator('#btnHost').waitFor({state: 'attached', timeout: 45000});
  await page.waitForTimeout(3000);
  const brokenImages = await page.evaluate(() => [...document.querySelectorAll('img[src]')]
    .filter(el => el.getAttribute('src')?.includes(String.fromCharCode(36,123,117,114,108,125)))
    .slice(0, 5).map(el => ({
      html: el.outerHTML.slice(0, 500),
      parent: el.parentElement?.outerHTML.slice(0, 650)
    })));
  if (brokenImages.length) console.log(label, 'broken image elements:', JSON.stringify(brokenImages));
  if (errors.length) throw Error(label + ' JavaScript exceptions: ' + errors.join(' | '));
  console.log('PASS', label, 'boot, menu visible, no uncaught JavaScript errors');
}

try {
  // Desktop smoke checks that touch changes do not disturb PC boot.
  const pc = await browser.newContext({viewport: {width: 1365, height: 768}});
  const desktop = await pc.newPage();
  await boot(desktop, 'desktop');
  const desktopPointer = await desktop.evaluate(() => matchMedia('(pointer:coarse)').matches);
  assert.equal(desktopPointer, false, 'PC incorrectly flagged as touch');
  await pc.close();

  const mobileContext = await browser.newContext({
    viewport: {width: 844, height: 390},
    isMobile: true, hasTouch: true, deviceScaleFactor: 1
  });
  const mobile = await mobileContext.newPage();
  await mobile.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== new URL(base).origin || (url.pathname !== '/' && url.pathname !== '/index.html')) {
      return route.continue();
    }
    const fetched = await route.fetch();
    const html = await fetched.text();
    return route.fulfill({response: fetched, body: withHooks(html)});
  });
  await boot(mobile, 'mobile');
  await mobile.waitForFunction(() => Boolean(window.__strykeMobileSmoke), {timeout: 45000});
  assert.equal(await mobile.evaluate(() => window.__strykeMobileSmoke.isMobile()), true,
    'mobile pointer should be coarse');
  await mobile.evaluate(() => window.__strykeMobileSmoke.prepare());
  await mobile.locator('#mobileControls').waitFor({state:'visible', timeout:12000});
  console.log('PASS mobile touch controls activated');

  // Real pointerdown/up browser events, so pointer capture is tested as well.
  async function fingerHold(locator, during, after) {
    const rect = await locator.boundingBox();
    assert(rect && rect.width && rect.height, 'control has no hit area');
    await mobile.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
    await mobile.mouse.down();
    try {
      assert.equal(await mobile.evaluate(during), true, 'hold-down did not set expected input');
    } finally {
      await mobile.mouse.up();
    }
    assert.equal(await mobile.evaluate(after), true, 'pointer release did not clear held input');
  }
  await fingerHold(mobile.locator('#mUse'),
    () => window.__strykeMobileSmoke.state().e,
    () => !window.__strykeMobileSmoke.state().e);
  console.log('PASS rounds: hold E, release E');

  await mobile.evaluate(() => window.__strykeMobileSmoke.setZombie(true));
  await fingerHold(mobile.locator('#mUse'),
    () => window.__strykeMobileSmoke.state().f,
    () => !window.__strykeMobileSmoke.state().f);
  console.log('PASS zombies: hold F, release F');

  await mobile.evaluate(() => window.__strykeMobileSmoke.setZombie(false));
  await mobile.locator('#mBuy').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).buy, true,
    'shop did not open');
  await mobile.locator('#mCloseBuy').waitFor({state: 'visible', timeout: 12000});
  assert.equal(await mobile.evaluate(() => {
    const el = document.querySelector('#mCloseBuy');
    const r = el.getBoundingClientRect();
    return document.elementFromPoint(r.left+r.width/2, r.top+r.height/2) === el;
  }), true, 'mobile shop close button is covered by another layer');
  await mobile.locator('#mCloseBuy').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).buy, false,
    'shop did not close');
  console.log('PASS shop: opens, has touch-accessible close button, closes');

  await mobile.locator('#mPause').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).paused, true,
    'pause did not open');
  await mobile.locator('#btnResume').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).paused, false,
    'resume did not dismiss pause');
  console.log('PASS pause: opens and resume dismisses overlay');

  await mobileContext.close();
  console.log('RESULT: All desktop + mobile smoke assertions passed');
} catch (error) {
  console.error('SMOKE FAIL:', error.stack || error);
  process.exitCode = 1;
} finally {
  await browser.close();
}
 + '{url}'))
    .slice(0, 5).map(el => ({
      html: el.outerHTML.slice(0, 500),
      parent: el.parentElement?.outerHTML.slice(0, 650)
    })));
  if (brokenImages.length) console.log(label, 'broken image elements:', JSON.stringify(brokenImages));
  if (errors.length) throw Error(label + ' JavaScript exceptions: ' + errors.join(' | '));
  console.log('PASS', label, 'boot, menu visible, no uncaught JavaScript errors');
}

try {
  // Desktop smoke checks that touch changes do not disturb PC boot.
  const pc = await browser.newContext({viewport: {width: 1365, height: 768}});
  const desktop = await pc.newPage();
  await boot(desktop, 'desktop');
  const desktopPointer = await desktop.evaluate(() => matchMedia('(pointer:coarse)').matches);
  assert.equal(desktopPointer, false, 'PC incorrectly flagged as touch');
  await pc.close();

  const mobileContext = await browser.newContext({
    viewport: {width: 844, height: 390},
    isMobile: true, hasTouch: true, deviceScaleFactor: 1
  });
  const mobile = await mobileContext.newPage();
  await mobile.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== new URL(base).origin || (url.pathname !== '/' && url.pathname !== '/index.html')) {
      return route.continue();
    }
    const fetched = await route.fetch();
    const html = await fetched.text();
    return route.fulfill({response: fetched, body: withHooks(html)});
  });
  await boot(mobile, 'mobile');
  await mobile.waitForFunction(() => Boolean(window.__strykeMobileSmoke), {timeout: 45000});
  assert.equal(await mobile.evaluate(() => window.__strykeMobileSmoke.isMobile()), true,
    'mobile pointer should be coarse');
  await mobile.evaluate(() => window.__strykeMobileSmoke.prepare());
  await mobile.locator('#mobileControls').waitFor({state:'visible', timeout:12000});
  console.log('PASS mobile touch controls activated');

  // Real pointerdown/up browser events, so pointer capture is tested as well.
  async function fingerHold(locator, during, after) {
    const rect = await locator.boundingBox();
    assert(rect && rect.width && rect.height, 'control has no hit area');
    await mobile.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
    await mobile.mouse.down();
    try {
      assert.equal(await mobile.evaluate(during), true, 'hold-down did not set expected input');
    } finally {
      await mobile.mouse.up();
    }
    assert.equal(await mobile.evaluate(after), true, 'pointer release did not clear held input');
  }
  await fingerHold(mobile.locator('#mUse'),
    () => window.__strykeMobileSmoke.state().e,
    () => !window.__strykeMobileSmoke.state().e);
  console.log('PASS rounds: hold E, release E');

  await mobile.evaluate(() => window.__strykeMobileSmoke.setZombie(true));
  await fingerHold(mobile.locator('#mUse'),
    () => window.__strykeMobileSmoke.state().f,
    () => !window.__strykeMobileSmoke.state().f);
  console.log('PASS zombies: hold F, release F');

  await mobile.evaluate(() => window.__strykeMobileSmoke.setZombie(false));
  await mobile.locator('#mBuy').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).buy, true,
    'shop did not open');
  await mobile.locator('#mCloseBuy').waitFor({state: 'visible', timeout: 12000});
  assert.equal(await mobile.evaluate(() => {
    const el = document.querySelector('#mCloseBuy');
    const r = el.getBoundingClientRect();
    return document.elementFromPoint(r.left+r.width/2, r.top+r.height/2) === el;
  }), true, 'mobile shop close button is covered by another layer');
  await mobile.locator('#mCloseBuy').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).buy, false,
    'shop did not close');
  console.log('PASS shop: opens, has touch-accessible close button, closes');

  await mobile.locator('#mPause').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).paused, true,
    'pause did not open');
  await mobile.locator('#btnResume').click({timeout: 12000});
  assert.equal((await mobile.evaluate(() => window.__strykeMobileSmoke.state())).paused, false,
    'resume did not dismiss pause');
  console.log('PASS pause: opens and resume dismisses overlay');

  await mobileContext.close();
  console.log('RESULT: All desktop + mobile smoke assertions passed');
} catch (error) {
  console.error('SMOKE FAIL:', error.stack || error);
  process.exitCode = 1;
} finally {
  await browser.close();
}
