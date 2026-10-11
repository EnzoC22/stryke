#!/usr/bin/env python3
"""Inspect STRYKE V44.1 multiplayer paths without changing game code."""
from pathlib import Path
import re

lines = Path("index.html").read_text(encoding="utf-8").splitlines()
patterns = [
    r"\b(?:const|let|var)\s+(?:NET|LB|RC|S|C)\s*=",
    r"function\s+(?:lobby\w*|join\w*|host\w*|srvStartMatch|srvStartRound|srvEndRound|srvRoundEnd|srvHandle|srvRecv|srvStart|net\w*|show\w*Lobby|enterGame|leaveGame|buildMap|syncBots|sendToHost|setTeam|teamPick)\s*\(",
    r"new Peer\s*\(",r"NET\.peer",r"\.on\(['\"](?:open|connection|data|close|error|disconnected)['\"]",
    r"\bbtnHost\b",r"\bbtnJoin\b",r"\bbtnResume\b",r"data-tab=.play.",r"LB\s*=",
    r"\b(?:function|const)\s+(?:startHost|joinRoom|createRoom|createLobby|lobbyHost|lobbyJoin|onMessage|handleMessage|peerOpen|peerConnect)\b",
    r"function\s+srv\w+\s*\(",r"(?:RC|BOMB)\s*=",
]
indexes=set()
print("TOTAL LINES",len(lines))
for p in patterns:
    found=[i for i,l in enumerate(lines) if re.search(p,l,re.I)]
    print("PATTERN",p,"MATCHES",len(found),"LINE_IDS",[i+1 for i in found[:65]])
    indexes.update(found[:36])
for i in sorted(indexes):
    print("CTX",i+1,repr("\n".join(f"{j+1}: {lines[j]}" for j in range(max(0,i-2),min(len(lines),i+5))))[:1900])
for needle in ("const NET =", "const LB =", "function lobbyHost", "function lobbyJoin", "function lobbyStart", "function srvStartMatch", "function srvStartRound", "function srvEndRound", "function sendToHost", "function enterGame", "new Peer("):
    ids=[i for i,l in enumerate(lines) if needle in l]
    for i in ids[:2]:
        print("DETAIL",needle,"LINE",i+1)
        print("\n".join(f"{j+1}: {lines[j]}" for j in range(max(0,i-5),min(len(lines),i+55)))[:12500])
