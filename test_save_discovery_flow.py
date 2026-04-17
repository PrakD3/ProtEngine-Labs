#!/usr/bin/env python3
"""Test the full Save Discovery flow: create analysis -> save discovery -> verify in DB"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_save_discovery_flow():
    """Test end-to-end: create session -> save discovery -> verify DB"""
    
    print("\n" + "="*70)
    print("TESTING: Save Discovery Flow (End-to-End)")
    print("="*70)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create analysis session
        print("\n[STEP 1] Creating analysis session...")
        try:
            async with session.post(
                f"{BASE_URL}/api/analyze",
                json={"query": "Test EGFR mutation L858R", "mode": "full"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    print(f"❌ FAILED: {resp.status} - {data}")
                    return
                
                session_id = data.get("session_id")
                print(f"✅ Session created: {session_id}")
                print(f"   Query: {data['query']}")
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return
        
        # Step 2: Wait a bit for session to initialize and populate
        print("\n[STEP 2] Waiting for session initialization (5 seconds)...")
        await asyncio.sleep(5)
        
        # Step 3: Try to save discovery (should work even without full analysis)
        print("\n[STEP 3] Saving discovery...")
        try:
            async with session.post(
                f"{BASE_URL}/api/discoveries/{session_id}/save",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
                
                if resp.status == 404:
                    print(f"❌ FAILED (404): {data['detail']}")
                    print("   → Session not found in memory (expired or not initialized)")
                    return
                elif resp.status == 500:
                    print(f"❌ FAILED (500): {data['detail']}")
                    print("   → Database save failed or not configured")
                    return
                elif resp.status == 200:
                    discovery_id = data.get("discovery_id")
                    print(f"✅ Discovery saved: {discovery_id}")
                else:
                    print(f"❌ FAILED ({resp.status}): {data}")
                    return
        except Exception as e:
            print(f"❌ Error saving discovery: {e}")
            return
        
        # Step 4: Verify discovery in database
        print("\n[STEP 4] Verifying discovery in database...")
        try:
            async with session.get(
                f"{BASE_URL}/api/discoveries/{discovery_id}",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    discovery = await resp.json()
                    print(f"✅ Discovery retrieved from DB:")
                    print(f"   ID: {discovery.get('id')}")
                    print(f"   Session ID: {discovery.get('session_id')}")
                    print(f"   Query: {discovery.get('query')}")
                    print(f"   Created: {discovery.get('created_at')}")
                    return True
                else:
                    print(f"❌ Failed to retrieve discovery: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Error retrieving discovery: {e}")
            return False

async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("SAVE DISCOVERY FLOW TEST SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)
    
    # Check backend health first
    print("\n[PRE-TEST] Checking backend health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    health = await resp.json()
                    print(f"✅ Backend is alive: {health}")
                else:
                    print(f"❌ Backend returned {resp.status}")
                    return
    except Exception as e:
        print(f"❌ Cannot reach backend: {e}")
        print("   Make sure backend is running: uvicorn main:app --reload")
        return
    
    # Run main test
    success = await test_save_discovery_flow()
    
    if success:
        print("\n" + "="*70)
        print("✅ TEST PASSED: Save Discovery flow is working!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST FAILED: See details above")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
