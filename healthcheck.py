#!/usr/bin/env python3
"""
Container healthcheck for ZimFire Monitor.

The worker writes (or rewrites) output/ranked_fire_alerts.csv on every
monitoring cycle. We treat the container as healthy if that file has
been touched within roughly 3 polling intervals. This tolerates the
occasional slow/failed cycle without flapping. During the initial
download the file may not exist yet; the Dockerfile's --start-period
covers that window, so a missing file there is reported unhealthy only
after the grace period.
"""
import os
import sys
import time
from pathlib import Path

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
POLL = int(os.getenv("POLL_INTERVAL_SECONDS", "900"))
# Allow 3 cycles of slack plus a fixed buffer for a long first cycle.
MAX_AGE = POLL * 3 + 600

marker = Path(OUTPUT_DIR) / "ranked_fire_alerts.csv"

if not marker.exists():
    print(f"unhealthy: {marker} not written yet")
    sys.exit(1)

age = time.time() - marker.stat().st_mtime
if age > MAX_AGE:
    print(f"unhealthy: {marker} stale ({int(age)}s > {MAX_AGE}s)")
    sys.exit(1)

print(f"healthy: {marker} age {int(age)}s")
sys.exit(0)
