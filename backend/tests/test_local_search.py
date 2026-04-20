import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append("/home/rafan/HF26-24/backend")

async def test_search():
    from routers.search import _search_local
    print("Testing local search for 'EGFR'...")
    try:
        results = await _search_local("EGFR", 1000000)
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
