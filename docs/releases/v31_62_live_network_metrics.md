# v31.62 Live Network Metrics

The native Jarvis system panel now replaces its static network examples with
read-only upload and download rates from psutil counters. A stateful sampler
computes rates between the existing five-second system refreshes using a
monotonic clock.

The first sample is zero because no interval exists yet. Counter resets and
provider failures are bounded to zero or `Unavailable`; counters and rates are
never persisted or transmitted.
