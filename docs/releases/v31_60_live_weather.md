# v31.60 Live Weather

The native Jarvis desktop no longer displays invented weather values. A
timeout-bounded background request reads current conditions from Open-Meteo and
updates the Tk interface without blocking its event loop. Refreshes run every
15 minutes.

Weather is opt-in through `SECONDBRAIN_WEATHER_LAT`,
`SECONDBRAIN_WEATHER_LON` and optional `SECONDBRAIN_WEATHER_PLACE`. Missing
configuration and transport failures produce explicit, redacted UI states.
