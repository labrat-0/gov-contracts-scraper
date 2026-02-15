"""Local test script -- tests all 3 scraping modes against live SAM.gov API.

Run: .venv/bin/python test_local.py YOUR_SAM_GOV_API_KEY

This bypasses the Apify Actor wrapper and tests the core scraping logic directly.
Requires a valid SAM.gov public API key as the first argument.
"""

import asyncio
import json
import sys
import time

import httpx

# Add src to path so we can import directly
sys.path.insert(0, ".")

from src.models import ScraperInput, ScrapingMode
from src.scraper import SamGovScraper
from src.utils import RateLimiter


async def test_mode(name: str, config: ScraperInput, max_items: int = 5) -> bool:
    """Test a single scraping mode. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

    rate_limiter = RateLimiter(interval=1.0)

    async with httpx.AsyncClient() as client:
        scraper = SamGovScraper(client, rate_limiter, config)

        items = []
        try:
            async for item in scraper.scrape():
                items.append(item)
                if len(items) >= max_items:
                    break
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False

    if not items:
        print(f"  FAIL: No items returned")
        return False

    print(f"  OK: Got {len(items)} items")
    # Print first item as sample
    print(f"  Sample item:")
    sample = json.dumps(items[0], indent=2, default=str)
    # Truncate long output
    if len(sample) > 800:
        sample = sample[:800] + "\n  ..."
    print(f"  {sample}")

    return True


async def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python test_local.py YOUR_SAM_GOV_API_KEY")
        print("")
        print("Get a free API key at https://sam.gov (Account Details > Public API Key)")
        sys.exit(1)

    api_key = sys.argv[1]
    results = {}
    start = time.time()

    # Test 1: Search Opportunities (cybersecurity)
    config = ScraperInput(
        api_key=api_key,
        mode=ScrapingMode.SEARCH_OPPORTUNITIES,
        keyword="cybersecurity",
        max_results=5,
    )
    results["search_opportunities"] = await test_mode(
        "Search Opportunities ('cybersecurity')", config, max_items=5
    )

    # Test 2: Search Awards
    config = ScraperInput(
        api_key=api_key,
        mode=ScrapingMode.SEARCH_AWARDS,
        keyword="software",
        max_results=5,
    )
    results["search_awards"] = await test_mode(
        "Search Awards ('software')", config, max_items=5
    )

    # Test 3: Entity Lookup
    config = ScraperInput(
        api_key=api_key,
        mode=ScrapingMode.ENTITY_LOOKUP,
        organization_name="Department of Defense",
        max_results=5,
    )
    results["entity_lookup"] = await test_mode(
        "Entity Lookup ('Department of Defense')", config, max_items=5
    )

    # Summary
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"RESULTS ({elapsed:.1f}s)")
    print(f"{'='*60}")
    all_passed = True
    for mode, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {mode}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"\nAll tests passed.")
    else:
        print(f"\nSome tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
