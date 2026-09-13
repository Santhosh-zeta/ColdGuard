"""
Helper script to generate all 10 synthetic CSV scenario files.
Run from the repository root: python data/raw/generate_scenarios.py
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
START = datetime(2024, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
N_HOURS = 168  # 7 days


def timestamps():
    return [START + timedelta(hours=h) for h in range(N_HOURS + 1)]


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


rng = np.random.default_rng(42)


def write(name, temps):
    ts = timestamps()
    rows = [{"timestamp": iso(t), "temperature_celsius": round(float(tc), 3)}
            for t, tc in zip(ts, temps)]
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False)
    print(f"  wrote {path}")


# 1. normal_cold_storage
n = N_HOURS + 1
base = 4.0 + rng.normal(0, 0.3, n)
write("normal_cold_storage.csv", base)

# 2. brief_excursion_15c  (4-hr excursion to 15°C at hour 48)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(48, 52):
    temps[h] = 15.0 + rng.normal(0, 0.3)
write("brief_excursion_15c.csv", temps)

# 3. extended_excursion_25c  (24-hr excursion to 25°C at hour 72)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(72, 96):
    temps[h] = 25.0 + rng.normal(0, 0.5)
write("extended_excursion_25c.csv", temps)

# 4. multiple_excursions (12°C/6hr at h20, 18°C/3hr at h80, 14°C/8hr at h130)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(20, 26):
    temps[h] = 12.0 + rng.normal(0, 0.4)
for h in range(80, 83):
    temps[h] = 18.0 + rng.normal(0, 0.4)
for h in range(130, 138):
    temps[h] = 14.0 + rng.normal(0, 0.4)
write("multiple_excursions.csv", temps)

# 5. near_freeze  (dip to 0.5°C for 3 hours at h36)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(36, 39):
    temps[h] = 0.5 + rng.normal(0, 0.1)
write("near_freeze.csv", temps)

# 6. logging_gap  (skip hours 60–68 — fewer rows)
ts_full = timestamps()
temps = 4.0 + rng.normal(0, 0.3, n)
rows = []
for h, (t, tc) in enumerate(zip(ts_full, temps)):
    if 60 < h < 68:
        continue
    rows.append({"timestamp": iso(t), "temperature_celsius": round(float(tc), 3)})
df = pd.DataFrame(rows)
path = os.path.join(OUT_DIR, "logging_gap.csv")
df.to_csv(path, index=False)
print(f"  wrote {path}")

# 7. transport_scenario  (rises to 22°C over 4 hours at h50, drops back)
temps = 4.0 + rng.normal(0, 0.3, n)
for i, h in enumerate(range(50, 54)):
    temps[h] = 4 + (22 - 4) * (i + 1) / 4 + rng.normal(0, 0.5)
for i, h in enumerate(range(54, 58)):
    temps[h] = 22 - (22 - 4) * (i + 1) / 4 + rng.normal(0, 0.5)
write("transport_scenario.csv", temps)

# 8. outreach_scenario  (3-hr period at 35°C at h100)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(100, 103):
    temps[h] = 35.0 + rng.normal(0, 0.5)
write("outreach_scenario.csv", temps)

# 9. freeze_event  (−5°C for 2 hours at h24)
temps = 4.0 + rng.normal(0, 0.3, n)
for h in range(24, 26):
    temps[h] = -5.0 + rng.normal(0, 0.2)
write("freeze_event.csv", temps)

# 10. worst_case  (4°C for 24hr, then 20°C for 48hr, then 4°C)
temps = np.where(
    np.arange(n) < 24,
    4.0,
    np.where(np.arange(n) < 72, 20.0, 4.0),
).astype(float)
temps += rng.normal(0, 0.3, n)
write("worst_case.csv", temps)

print("All 10 scenario files generated.")
