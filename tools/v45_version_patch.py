from pathlib import Path
p=Path("index.html")
s=p.read_text(encoding="utf-8")
old="STRYKE <b>4.8 // V44 COMPETITIVE FOUNDATION</b>"
new="STRYKE <b>4.9 // V45 TACTICAL MAPS</b>"
if s.count(old)!=1:raise SystemExit("Unexpected version label, refusing update")
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")
print("V45 release chip updated")
