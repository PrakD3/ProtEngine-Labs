#!/usr/bin/env python3
"""Debug Save Discovery - trace the issue"""

import urllib.request
import json
import time
import sys

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("DEBUG: Save Discovery Flow")
print("="*70)

# Step 1: Create analysis
print("\n[1] Creating analysis session...")
req = urllib.request.Request(
    f"{BASE_URL}/api/analyze",
    data=json.dumps({"query": "EGFR L858R", "mode": "full"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    session_id = result["session_id"]
    print(f"✅ Session ID: {session_id}")

# Step 2: Check if session exists in /api/stream
print(f"\n[2] Checking if session exists via /api/stream/{session_id}...")
time.sleep(1)
try:
    with urllib.request.urlopen(f"{BASE_URL}/api/stream/{session_id}") as resp:
        print(f"✅ Session exists - stream endpoint responding")
except urllib.error.HTTPError as e:
    print(f"❌ Stream endpoint error: HTTP {e.code}")
    print(f"   This means session_id {session_id} doesn't exist in backend memory")

# Step 3: Try to save immediately
print(f"\n[3] Trying to save discovery immediately...")
try:
    req = urllib.request.Request(
        f"{BASE_URL}/api/discoveries/{session_id}/save",
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"✅ Saved! Discovery ID: {result.get('discovery_id')}")
except urllib.error.HTTPError as e:
    error_data = json.loads(e.read())
    print(f"❌ HTTP {e.code}: {error_data['detail']}")
    print(f"\nDebugging:")
    print(f"  - Session ID sent: {session_id}")
    print(f"  - Error message: {error_data['detail']}")
    print(f"  - This suggests: session not found in _sessions dict")
    print(f"\nPossible causes:")
    print(f"  1. analysis.py not initializing session in _sessions")
    print(f"  2. Different _sessions dict imported in analysis.py vs discoveries.py")
    print(f"  3. Background task hasn't started yet")
