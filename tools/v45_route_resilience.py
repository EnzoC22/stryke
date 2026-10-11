#!/usr/bin/env python3
"""Read-only tactical 5v5 grid audit: detect single-tile bottlenecks and arrival imbalance.

Grid measurements are screening signals, not substitutes for Chromium physics,
pre-round barriers, collision, and real movement speeds. Never edits game data.
"""
import collections
import json
import re
import sys
from pathlib import Path

NAMES = ('vanta', 'frostline', 'kairo', 'cargo')
SOLID = frozenset('#cquvhipbxk')  # match stryke_improvement_cycle.py
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def read_maps(source):
    maps = {}
    for name in NAMES:
        found = list(re.finditer(r'MAPS\.' + name + r'\s*=\s*gridMap\(\[\s*(.*?)\s*\],\s*([\d.]+)', source, re.S))
        if not found:
            raise ValueError(f'Missing active map: {name}')
        match = found[-1]  # most recent map assignment wins at runtime
        rows = re.findall(r"'([#.\w]+)'", match.group(1))
        if not rows or len({len(row) for row in rows}) != 1:
            raise ValueError(f'Invalid grid rows: {name}')
        maps[name] = (rows, float(match.group(2)))
    return maps


def search(rows, start, targets, banned=None):
    """Multi-source shortest grid route. Return cell path, or None."""
    height, width = len(rows), len(rows[0])

    def open_cell(p):
        r, c = p
        return (0 <= r < height and 0 <= c < width and
                rows[r][c] not in SOLID and p != banned)

    ends = set(targets)
    queue = collections.deque(p for p in start if open_cell(p))
    parent = {p: None for p in queue}
    while queue:
        point = queue.popleft()
        if point in ends:
            path = []
            while point is not None:
                path.append(point)
                point = parent[point]
            return path[::-1]
        for dr, dc in DIRS:
            nxt = (point[0] + dr, point[1] + dc)
            if nxt not in parent and open_cell(nxt):
                parent[nxt] = point
                queue.append(nxt)
    return None


def analyze(name, rows, scale):
    cells = {k: [] for k in 'TCAB'}
    for r, row in enumerate(rows):
        for c, mark in enumerate(row):
            if mark in cells:
                cells[mark].append((r, c))
    if any(not cells[k] for k in cells):
        raise ValueError(f'{name}: missing T, C, A or B cells')
    report = {'map': name, 'grid': [len(rows[0]), len(rows)], 'units_per_cell': scale,
              'routes': {}, 'warnings': []}
    for team in 'TC':
        for site in 'AB':
            key = f'{team}_to_{site}'
            path = search(rows, cells[team], cells[site])
            if path is None:
                raise ValueError(f'{name}: {team} has no path to {site}')
            # Exclude spawn and site footprints from neutral-route choke analysis.
            internal = [p for p in path[1:-1] if rows[p[0]][p[1]] not in 'TCAB']
            cuts = [p for p in internal if search(rows, cells[team], cells[site], banned=p) is None]
            report['routes'][key] = {
                'distance_cells': len(path) - 1,
                'distance_units_est': round((len(path) - 1) * scale, 1),
                'single_tile_cuts': len(cuts),
                'cut_cells': [list(p) for p in cuts[:8]],
            }
            if cuts:
                report['warnings'].append(f'{key}: {len(cuts)} unavoidable one-tile choke(s) in grid')
    for site in 'AB':
        t = report['routes'][f'T_to_{site}']['distance_units_est']
        ct = report['routes'][f'C_to_{site}']['distance_units_est']
        lead = round(t - ct, 1)
        report.setdefault('ct_lead_units_est', {})[site] = lead
        if abs(lead) > 27:
            report['warnings'].append(f'{site}: arrival lead {lead:+.1f} units; review in Chromium')
    return report


def main():
    source = Path('index.html').read_text(encoding='utf-8')
    results = [analyze(name, *value) for name, value in read_maps(source).items()]
    print(json.dumps({'maps': results,
                      'note': 'Grid-only heuristic; confirm browser collision/barriers before edits'},
                     ensure_ascii=False, indent=2))
    count = sum(len(r['warnings']) for r in results)
    print(f'PASS route resilience audit: {len(results)} maps; {count} nonblocking review signals')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'FAIL route resilience audit: {exc}', file=sys.stderr)
        sys.exit(1)
