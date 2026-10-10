#!/usr/bin/env python3
"""Read-only snapshot audit of STRYKE V44 map / round / bot anchors."""
from pathlib import Path
import re
s=Path("index.html").read_text(encoding="utf-8")
print("STRYKE V44 READ-ONLY MAP AUDIT")
print("bytes",len(s.encode()),"chars",len(s),"lines",s.count("\n")+1)
queries = [
 ("map declarations",r"(?:const|let|var)\s+(?:MAPS|MAP|MAP_DATA|MAP_DEF|MAP_DEFS|ARENAS)\s*="),
 ("map init",r"(?:function|const)\s+(?:buildMap|loadMap|createMap|buildArena|genMap|spawnMap|mapBuild|navBuild|buildNav|navPath|pathfind|findPath|worldToGrid|gridToWorld|mapPath)\b"),
 ("spawn / site",r"(?:function|const)\s+\w*(?:Spawn|Site|Bomb|Barrier|Nav|Collis|Cover|Route|Path)\w*\s*\("),
 ("bot path",r"(?:function|const)\s+\w*(?:bot|Bot|BOT)\w*\s*\("),
 ("competitive map names",r"(?:(?:vanta|frostline|kairo|cargo)\s*:\s*\{|(?:vanta|frostline|kairo|cargo)\s*:\s*\w+)"),
 ("spawn data keys",r"(?:spT|spCT|tSpawn|ctSpawn|spawnT|spawnCT|bombA|bombB|sites|spawn|siteA|siteB)\s*:"),
 ("wall / collision constants",r"(?:const|let)\s+\w*(?:COLLISION|WALKABLE|NAV|WALL|SPAWN|SITE)\w*\s*="),
 ("match setup",r"(?:function|const)\s+(?:srvStartMatch|lobbyStart|startRound|srvRoundStart|srvPlant|srvDefuse|srvStartRound|roundStart|enterGame)\b"),
]
for title,pat in queries:
    print("\n###",title)
    matches=list(re.finditer(pat,s,re.I if "spawn / site"==title else 0))
    print("total",len(matches))
    for m in matches[:25 if title != "spawn data keys" else 16]:
        ctx=s[max(0,m.start()-135):min(len(s),m.end()+500)]
        print("AT",m.start(),"LINE",s.count("\n",0,m.start())+1,repr(ctx))
print("\n### FIRST OCCURRENCE GRID AND MAP SETUP")
for word in ("const MAPS", "const MAP_IDS", "const MAP=", "createMap(", "buildMap(", "mapId", "curMapId", "spawnT", "ctSpawn", "GRID", "NAV", "pathfind", "getSpawn", "walkable", "bombSites", "SPAWN", "MAP_LAYOUTS", "mapSpecs"):
    pos=s.find(word)
    if pos>=0: print(word,"AT",pos,"CONTEXT",repr(s[max(0,pos-200):pos+1100]))

print("\n### MAP ASSIGNMENTS / OVERRIDES")
for pat in [r"MAPS\.(?:vanta|frostline|kairo|cargo)\s*=",r"Object\.assign\(MAPS",r"\.spawns\s*=",r"\.sites\s*=",r"SPAWNS\.a\s*=",r"SPAWNS\.b\s*=",r"SPAWNS\[",r"buildNav\(",r"navPath\("]:
    print("PATTERN",pat)
    found=list(re.finditer(pat,s))
    print("COUNT",len(found))
    for m in found[:18]:
        print("AT",m.start(),"LINE",s.count("\n",0,m.start())+1,"CTX",repr(s[max(0,m.start()-200):m.start()+360]))
print("\n### COMPLETE NAV BLOCK")
a=s.find("function buildNav(M)");b=s.find("// ----------",a+20)
print(s[a:min(a+5600,b if b>=0 else a+5600)])
print("\n### BUILD MAP SPAWNS")
a=s.find("function buildMap(id)")
for marker in ("SPAWNS.a","SPAWNS.b","buildNav(","COL.push","M.boxes","SPAWNS["):
    x=s.find(marker,a)
    if x>=0 and x<a+16000:
        print("BUILD MAP", marker,repr(s[x-400:x+900]))
