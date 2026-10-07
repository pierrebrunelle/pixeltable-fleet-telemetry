"""Seed 60 synthetic readings for 6 vehicles in 2 fleets.

Usage:
    python seed.py            # seeds the local `fleet` catalog directory
    python seed.py my_dir     # or another directory you passed to `pxt schema update`
"""
import sys
from pathlib import Path

import pixeltable as pxt

target = sys.argv[1] if len(sys.argv) > 1 else 'fleet'
HERE = Path(__file__).resolve().parent

import random

random.seed(7)
SEED = {'readings': []}
for i in range(60):
    v = i % 6
    SEED['readings'].append({
        'vehicle_id': f'V{100 + v}', 'fleet': 'north' if v < 3 else 'south',
        'status': random.choice(['moving', 'moving', 'idle', 'parked']),
        'recorded_at': f'2026-09-27T{8 + i // 10:02d}:{(i * 7) % 60:02d}:00',
        'speed_kph': round(random.uniform(0, 135), 1), 'engine_temp_c': round(random.uniform(80, 118), 1),
        'fuel_pct': round(random.uniform(4, 95), 1),
    })

for table_name, rows in SEED.items():
    t = pxt.get_table(f'{target}/{table_name}')
    if t.count() > 0:
        print(f'{target}/{table_name} already has {t.count()} rows; skipping')
        continue
    for row in rows:
        for k, v in row.items():
            if isinstance(v, str) and v.startswith('data/'):
                row[k] = str(HERE / v)   # local sample media file
    t.insert(rows)
    print(f'inserted {len(rows)} rows into {target}/{table_name}')
