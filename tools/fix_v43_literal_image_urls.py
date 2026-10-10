from pathlib import Path

p = Path('index.html')
original = p.read_text(encoding='utf-8')
before = """('<img src="' + url + '" alt="">')"""
after = """('<' + 'img src="' + url + '" alt="">')"""
count = original.count(before)
if count != 2:
    raise SystemExit('Refusing parser preload fix: expected exactly 2 matches, found ' + str(count))
updated = original.replace(before, after)
if abs(len(updated) - len(original)) > 100:
    raise SystemExit('Refusing patch: unexpected size change')
p.write_text(updated, encoding='utf-8')
print('V43 image parser fix: split both raw img prefixes while preserving HTML output')
