#!/usr/bin/env python3
"""STRYKE V44.2: enforce bomb deadline before defuse action settlement.

Single-line guard in bombTick, deliberately does not change weapons, movement,
round timing constants, maps, anti-cheat rules or assets. Refuse unknown source.
"""
from pathlib import Path

path=Path("index.html")
old=path.read_text(encoding="utf-8")
start=old.find("function bombTick() {")
end=old.find("function srvBuy(",start)
if not 0 <= start < end < len(old) or end-start>7000:
    raise SystemExit("Unknown bombTick region; refusing to modify game")
region=old[start:end]
anchor="""    if (now < a.end) continue;
    p.act = null; p.money = Math.min(16000, p.money + 300);"""
replacement="""    if (now < a.end) continue;
    // V44.2: a defuse cannot win if its completion tick occurs after the bomb deadline.
    if (a.k === 'd' && B?.st === 'planted' && now >= B.end) { p.act = null; continue; }
    p.act = null; p.money = Math.min(16000, p.money + 300);"""
if region.count(anchor)!=1 or "V44.2: a defuse cannot win" in old:
    raise SystemExit("Unexpected or already-patched bombTick; refusing change")
next_code=old[:start]+region.replace(anchor,replacement,1)+old[end:]
if abs(len(next_code)-len(old))>260:
    raise SystemExit("Unexpected modification size")
path.write_text(next_code,encoding="utf-8")
print("V44.2: single bombTick guard added; expiry now takes priority over late defuse")
