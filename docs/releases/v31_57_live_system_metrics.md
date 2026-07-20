# v31.57 Live System Metrics

The native Jarvis desktop now replaces its static CPU, RAM, swap and disk
examples with read-only host metrics. Text values, metric rings, the CPU reactor
and disk utilization bar share the same snapshot and refresh every five seconds.

Metrics use the optional desktop `psutil` dependency. If it is missing or the
host query fails, the interface shows `Unavailable` and zeroed visual indicators
instead of presenting invented values.
