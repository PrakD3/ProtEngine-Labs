#!/usr/bin/env python3
"""Simple test of Save Discovery flow using urllib"""

import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("TESTING: Save Discovery Flow")
print("="*70)

# Step 1: Check health
print("\n[1] Checking backend health...")
try:
    with urllib.request.urlopen(f"{BASE_URL}/api/health") as resp:
        data = json.loads(resp.read())
        print(f"✅ Backend alive: {data}")
except Exception as e:
    print(f"❌ Backend error: {e}")
    exit(1)

# Step 2: Create analysis
print("\n[2] Creating analysis session...")
try:
    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=json.dumps({"query": "EGFR L858R", "mode": "full"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        session_id = result["session_id"]
        print(f"✅ Session created: {session_id}")
except Exception as e:
    print(f"❌ Failed to create session: {e}")
    exit(1)

# Step 3: Wait for session to populate and pipeline to complete
print("\n[3] Waiting 15 seconds for pipeline to complete and auto-save...")
time.sleep(15)

# Step 4: Save discovery
print(f"\n[4] Saving discovery from session {session_id}...")
try:
    req = urllib.request.Request(
        f"{BASE_URL}/api/discoveries/{session_id}/save",
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        discovery_id = result.get("discovery_id")
        print(f"✅ Saved! Discovery ID: {discovery_id}")
except urllib.error.HTTPError as e:
    error_data = json.loads(e.read())
    error_detail = error_data.get('detail', 'Unknown error')
    print(f"❌ HTTP {e.code}: {error_detail}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 5: Verify in database
print(f"\n[5] Verifying discovery in database...")
try:
    with urllib.request.urlopen(f"{BASE_URL}/api/discoveries/{discovery_id}") as resp:
        discovery = json.loads(resp.read())
        print(f"✅ Found in database!")
        print(f"   ID: {discovery.get('id')}")
        print(f"   Session: {discovery.get('session_id')}")
        print(f"   Query: {discovery.get('query')}")
        print(f"   Created: {discovery.get('created_at')}")
except Exception as e:
    print(f"❌ Not found: {e}")
    exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED - Save Discovery flow is working!")
print("="*70)
