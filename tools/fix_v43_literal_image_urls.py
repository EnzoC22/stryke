from pathlib import Path

p = Path('index.html')
original = p.read_text(encoding='utf-8')
placeholder = chr(36) + '{url}'
before = '`<img src="' + placeholder + '" alt="">`'
after = """('<img src="' + url + '" alt="">')"""
count = original.count(before)
if count != 2:
    raise SystemExit('Refusing V43 placeholder fix: expected 2 guarded matches, found ' + str(count))
updated = original.replace(before, after)
if abs(len(updated) - len(original)) > 200:
    raise SystemExit('Refusing patch: unexpected size change')
p.write_text(updated, encoding='utf-8')
print('V43 fix: replaced 2 markup templates with equivalent safe runtime string concatenation')
