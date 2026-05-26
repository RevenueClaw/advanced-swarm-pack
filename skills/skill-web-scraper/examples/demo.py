#!/usr/bin/env python3
"""
Web Scraper Demo - Showcase capabilities

Usage:
    python demo.py [command] [options]
    
Commands:
    scrape <url>          Scrape a specific URL
    test-stealth          Test against detection sites
    batch                 Batch scrape multiple URLs
    stats                 Show scraper statistics
    
Examples:
    python demo.py scrape https://example.com --engine nodriver
    python demo.py test-stealth
    python demo.py batch urls.txt
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.stealth_scraper import StealthScraper, ScrapeRequest
from lib.fingerprint_manager import FingerprintManager
from lib.behavior_engine import BehaviorEngine


async def demo_scrape(url: str, engine: str = "auto", human: bool = True):
    """Demonstrate single URL scraping."""
    print(f"\n{'='*60}")
    print(f"DEMO: Scraping {url}")
    print(f"{'='*60}")
    
    scraper = StealthScraper(preferred_engine=engine)
    
    request = ScrapeRequest(
        url=url,
        wait_time=3.0,
        human_behavior=human,
        wait_for="networkidle",
    )
    
    print(f"⏳ Scraping with engine: {engine}...")
    result = await scraper.scrape(request)
    
    print(f"\n✅ Success: {result.success}")
    print(f"📊 Confidence Score: {result.success_score}/100")
    print(f"🔧 Engine Used: {result.engine_used}")
    print(f"⏱️  Duration: {result.duration_seconds:.2f}s")
    
    if result.proxy_used:
        print(f"🌐 Proxy: {result.proxy_used}")
        
    if result.techniques_used:
        print(f"🛡️  Techniques: {', '.join(result.techniques_used)}")
        
    if result.blocks_encountered:
        print(f"⚠️  Blocks: {', '.join(result.blocks_encountered)}")
        
    if result.data:
        print(f"\n📄 Extracted Data:")
        print(json.dumps(result.data, indent=2)[:500] + "..." if len(json.dumps(result.data)) > 500 else "")
        
    if result.error:
        print(f"\n❌ Error: {result.error}")
        
    return result


async def demo_stealth_test():
    """Test stealth against detection sites."""
    test_sites = [
        ("httpbin.org", "https://httpbin.org/get"),
        ("User-Agent test", "https://httpbin.org/user-agent"),
        ("Headers test", "https://httpbin.org/headers"),
    ]
    
    print(f"\n{'='*60}")
    print("DEMO: Stealth Testing")
    print(f"{'='*60}")
    
    scraper = StealthScraper()
    
    for name, url in test_sites:
        print(f"\n🧪 Testing: {name}")
        result = await scraper.scrape(ScrapeRequest(url=url, wait_time=2))
        print(f"   Score: {result.success_score}/100 | Engine: {result.engine_used}")
        
        if result.data and 'origin' in str(result.data):
            print(f"   IP detected: {result.data.get('origin', 'N/A')}")


async def demo_fingerprint():
    """Demonstrate fingerprint generation."""
    print(f"\n{'='*60}")
    print("DEMO: Fingerprint Generation")
    print(f"{'='*60}")
    
    manager = FingerprintManager()
    
    for i in range(3):
        print(f"\n🎭 Profile {i+1}:")
        fp = manager.generate_fingerprint(
            mobile=(i == 2),
            os_hint="Windows" if i == 0 else "macOS"
        )
        
        print(f"   UA: {fp.user_agent[:60]}...")
        print(f"   Platform: {fp.platform}")
        print(f"   Viewport: {fp.viewport_width}x{fp.viewport_height}")
        print(f"   Timezone: {fp.timezone}")
        print(f"   Hardware: {fp.hardware_concurrency} cores, {fp.device_memory}GB RAM")
        print(f"   Graphics: {fp.renderer[:50]}...")


async def demo_behavior():
    """Demonstrate human behavior simulation."""
    print(f"\n{'='*60}")
    print("DEMO: Human Behavior Patterns")
    print(f"{'='*60}")
    
    engine = BehaviorEngine()
    
    print("\n⏱️  Delay patterns (5 samples):")
    for i in range(5):
        delay = []
        start = asyncio.get_event_loop().time()
        await engine.human_delay(1.0)
        actual = asyncio.get_event_loop().time() - start
        print(f"   Target: 1.0s | Actual: {actual:.2f}s")
        
    print("\n📐 Bezier curve preview:")
    from lib.behavior_engine import Point
    path = engine.generate_bezier_curve(
        Point(100, 100),
        Point(500, 400)
    )
    print(f"   Generated path with {len(path)} points")
    print(f"   Start: ({path[0].x:.0f}, {path[0].y:.0f})")
    print(f"   End: ({path[-1].x:.0f}, {path[-1].y:.0f})")


async def demo_batch(urls: List[str]):
    """Demonstrate batch scraping."""
    print(f"\n{'='*60}")
    print(f"DEMO: Batch Scraping ({len(urls)} URLs)")
    print(f"{'='*60}")
    
    scraper = StealthScraper()
    
    requests = [
        ScrapeRequest(url=url, wait_time=2)
        for url in urls
    ]
    
    print(f"⏳ Starting batch with concurrency=2, delay=3s...")
    results = await scraper.scrape_batch(
        requests,
        concurrency=2,
        delay_between=3.0
    )
    
    print(f"\n📊 Results Summary:")
    successful = sum(1 for r in results if r.success)
    print(f"   Success: {successful}/{len(results)}")
    print(f"   Avg Score: {sum(r.success_score for r in results) / len(results):.1f}")
    
    for i, (url, result) in enumerate(zip(urls, results)):
        status = "✅" if result.success else "❌"
        print(f"   {status} [{i+1}] {url[:40]}... ({result.engine_used}, {result.success_score}/100)")


async def main():
    parser = argparse.ArgumentParser(description="Web Scraper Demo")
    parser.add_argument("command", choices=["scrape", "test-stealth", "fingerprint", "behavior", "batch", "stats", "all"])
    parser.add_argument("--url", default="https://example.com")
    parser.add_argument("--engine", default="auto", choices=["auto", "nodriver", "playwright", "http"])
    parser.add_argument("--no-human", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "scrape":
        await demo_scrape(args.url, args.engine, human=not args.no_human)
        
    elif args.command == "test-stealth":
        await demo_stealth_test()
        
    elif args.command == "fingerprint":
        await demo_fingerprint()
        
    elif args.command == "behavior":
        await demo_behavior()
        
    elif args.command == "batch":
        urls = [
            "https://example.com",
            "https://httpbin.org/get",
            "https://httpbin.org/headers",
        ]
        await demo_batch(urls)
        
    elif args.command == "stats":
        scraper = StealthScraper()
        print(json.dumps(scraper.get_stats(), indent=2))
        
    elif args.command == "all":
        print("\n" + "="*60)
        print("RUNNING ALL DEMOS")
        print("="*60)
        
        await demo_fingerprint()
        await demo_behavior()
        await demo_stealth_test()
        await demo_scrape("https://example.com", "http", human=True)
        await demo_batch(["https://example.com", "https://httpbin.org/get"])
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETE")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
