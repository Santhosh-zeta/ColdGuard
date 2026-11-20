# Monte Carlo engine benchmarks

The benchmarks measure the existing Python Monte Carlo engine; they do not
change kinetic parameters or the scientific decision model.

## Run locally

From the repository root, using Python 3.11 or later:

```sh
python -m pip install -e ".[dev]"
python -m pytest tests/perf --benchmark-only --benchmark-sort=mean
```

The performance suite is opt-in: the regular `python -m pytest tests/`
command does not collect it. To save a machine-readable comparison baseline,
add `--benchmark-json=benchmark-results.json` to the benchmark command.

## Workloads

| Case | Samples | Temperature readings | Sample × reading elements |
| --- | ---: | ---: | ---: |
| Large log | 5,000 | 1,000 | 5,000,000 |
| Many samples | 20,000 | 100 | 2,000,000 |
| Mobile-sized input | 1,000 | 24 | 24,000 |

All cases use DPT parameters, hourly timestamps, a synthetic daily temperature
cycle of 4–6 °C, and seed 42. A new random generator is constructed before each
round, outside the measured function. The measurement includes random draws,
noise generation, freeze retention, trapezoidal integration and clipping.
There is one warmup round and seven measured rounds per case. Correctness
assertions run outside the measured interval.

The 24-reading case represents a small input to the **Python** engine, not
an actual Android timing or a comparison with the JavaScript implementation.

## Baseline results

Initial contributor-measured baseline (2026-11-20), in milliseconds per call:

| Case | Median (ms) | Mean (ms) | Std. dev. (ms) | Rounds |
| --- | ---: | ---: | ---: | ---: |
| Mobile-sized input | 1.9152 | 1.9163 | 0.1300 | 7 |
| Many samples | 257.0337 | 261.0607 | 41.8610 | 7 |
| Large log | 559.5165 | 616.4456 | 117.7548 | 7 |

Environment: Windows 11 (build 26300), Intel64 Family 6 Model 154
Stepping 4 (GenuineIntel), Python 3.13.3, NumPy 2.5.5, pytest 9.2.0,
pytest-benchmark 5.3.1. All three benchmark tests passed, and the separate
ordinary suite passed 155 tests without collecting the benchmarks.

This is one local run, not a hardware-independent performance guarantee.
The relatively large variation in the large-log and many-samples cases
makes repeated measurements useful before interpreting small changes.
No fixed timing threshold is used because execution time depends on
hardware and load. No phone or Linux timing is inferred from these results.

## Profiling and memory

The integration uses chunks of approximately 2,000,000 sample-reading elements.
However, the noise and perturbed temperature matrices are allocated for the
entire workload before chunking. For the large-log case, each such float64
matrix is 40,000,000 bytes (about 38.1 MiB), excluding other arrays.
The benchmark does not establish a peak-memory bound or prove that the existing
chunk size is optimal.

For regressions, compare repeated runs on the same hardware and software
versions. Profiling can identify the dominant calls separately from the
unprofiled baseline measurements.
