#!/usr/bin/env python3
"""Merge V46.1 bot benchmark shards, compute confidence intervals and optional baseline diffs.

This is analysis of diagnostic bots (not human competitive win probability).
No mutation to gameplay/source assets.
"""
import argparse
import json
import math
import os
from pathlib import Path

MAPS = ("vanta", "frostline", "kairo", "cargo")


def wilson(wins, total, z=1.96):
    if not total:
        return [None, None]
    rate = wins / total
    denom = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denom
    span = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denom
    return [round(max(0, center - span) * 100, 1),
            round(min(1, center + span) * 100, 1)]


def load_samples(directory):
    samples = []
    for name in MAPS:
        path = directory / f"v461-{name}.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        assert obj["map"] == name
        assert obj["replayPassed"] is True, f"{name}: deterministic replay was not proven"
        assert obj["roundsRequested"] == len(obj["rounds"]), f"{name}: incomplete dataset"
        assert all(r["winner"] in ("t", "ct") for r in obj["rounds"]), f"{name}: missing round"
        assert len({r["seed"] for r in obj["rounds"]}) == len(obj["rounds"]), f"{name}: duplicated seeds"
        samples.append(obj)
    counts = {len(obj["rounds"]) for obj in samples}
    assert len(counts) == 1, f"Different round counts across maps: {counts}"
    return samples


def rollup(shards):
    data = {"schema": 1, "version": "V46.1", "roundsPerMap": len(shards[0]["rounds"]),
            "baseSeed": shards[0]["baseSeed"], "commit": shards[0]["commit"],
            "method": "independent seeded bot-only rounds at fixed 100ms authoritative ticks",
            "warning": "Bot simulation is not a statistically representative human-player win rate.",
            "maps": {}}
    for source in shards:
        name = source["map"]
        s = dict(source["summary"])
        s["winPct95CI"] = wilson(s["wins"]["t"], s["count"])
        s["replayPassed"] = source["replayPassed"]
        deaths = [x["firstDeath"] for x in source["rounds"] if x["firstDeath"]]
        # Quantize position to 10x10 world-unit buckets; no player-identifying data.
        heat = {}
        for e in deaths:
            bucket = f'{math.floor(e["position"][0] / 10) * 10},{math.floor(e["position"][1] / 10) * 10}'
            heat[bucket] = heat.get(bucket, 0) + 1
        s["firstDeathHeatmap"] = dict(sorted(heat.items(), key=lambda x: -x[1])[:12])
        data["maps"][name] = s
    return data


def compare(previous, current):
    if not previous:
        return None
    if (previous.get("baseSeed") != current["baseSeed"] or
            previous.get("roundsPerMap") != current["roundsPerMap"]):
        return {"available": False, "reason": "Baseline seed/count differs; comparison skipped"}
    deltas = {}
    for name in MAPS:
        old, new = previous.get("maps", {}).get(name), current["maps"][name]
        if not old:
            continue
        deltas[name] = {
            "attackerWinPctDelta": round(new["attackerWinPct"] - old["attackerWinPct"], 1),
            "avgDurationDelta": round(new["avgDuration"] - old["avgDuration"], 1),
            "stallSignalsDelta": new["stallSignals"] - old["stallSignals"],
        }
    return {"available": bool(deltas), "baselineCommit": previous.get("commit"), "byMap": deltas}


def markdown(result):
    lines = ["# STRYKE V46.1 · Competitive bot benchmark", "",
             f'Commit: \`{result.get("commit") or "local"}\` · {result["roundsPerMap"]} seeded rounds per map',
             "",
             "| Map | T wins | CT wins | T win % (95% CI) | Mean round | Navigation stall signals |",
             "|---|---:|---:|---|---:|---:|"]
    for name, stat in result["maps"].items():
        lo, hi = stat["winPct95CI"]
        lines.append(f'| {name.title()} | {stat["wins"]["t"]} | {stat["wins"]["ct"]} | '
                     f'{stat["attackerWinPct"]}% ({lo}–{hi}%) | '
                     f'{stat["avgDuration"]}s | {stat["stallSignals"]} |')
    lines.extend(["", "**Interpretation:** simulations are real-engine bot-only diagnostics, not human-game win rates.",
                  "The benchmark validates replay determinism on each map before collecting results."])
    diff = result.get("comparison")
    if diff and diff.get("available"):
        lines.extend(["", f'Baseline commit: \`{diff["baselineCommit"]}\`', "",
                      "| Map | T win percentage-point change | Round duration change | Stall change |",
                      "|---|---:|---:|---:|"])
        for name, row in diff["byMap"].items():
            lines.append(f'| {name.title()} | {row["attackerWinPctDelta"]:+} pp | '
                         f'{row["avgDurationDelta"]:+}s | {row["stallSignalsDelta"]:+} |')
    elif diff and not diff.get("available"):
        lines.append(f'Baseline: {diff.get("reason", "not compatible")}')
    else:
        lines.append("No compatible baseline was available for this run.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--directory", default="reports")
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--output", default="reports/v461-summary.json")
    args = ap.parse_args()
    report_dir = Path(args.directory)
    previous = None
    if args.baseline and Path(args.baseline).is_file():
        previous = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    shards = load_samples(report_dir)
    result = rollup(shards)
    result["comparison"] = compare(previous, result)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = markdown(result)
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    # Save new baseline after reading old one, so the cache can carry it forward.
    if args.baseline:
        Path(args.baseline).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
