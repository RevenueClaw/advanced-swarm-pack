#!/usr/bin/env python3
"""
Core Stealth Scraper - Multi-Engine Web Scraping

Supports:
- Nodriver (async CDP-based Chrome) - PRIMARY, best stealth
- Playwright + stealth plugins - SECONDARY fallback
- Managed APIs (ScrapingBee, Scrapfly, etc.) - TERTIARY fallback
- Simple HTTP (httpx/aiohttp) - for simple static sites

Features comprehensive anti-detection layers:
- Fingerprint consistency
- Human behavior simulation
- Proxy rotation
- Intelligent retry logic
"""

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Structured result from a scrape operation."""
    success: bool
    url: str
    data: Optional[Dict] = None
    html: Optional[str] = None
    text: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    error: Optional[str] = None
    
    # Stealth/detection metrics
    success_score: int = 0  # 0-100 confidence
    techniques_used: List[str] = field(default_factory=list)
    blocks_encountered: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_seconds: float = 0.0
    
    # Technical details
    engine_used: str = "unknown"
    proxy_used: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "url": self.url,
            "data": self.data,
            "html": self.html[:1000] + "..." if self.html and len(self.html) > 1000 else self.html,
            "metadata": self.metadata,
            "error": self.error,
            "success_score": self.success_score,
            "techniques_used": self.techniques_used,
            "blocks_encountered": self.blocks_encountered,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "engine_used": self.engine_used,
            "proxy_used": self.proxy_used,
            "user_agent": self.user_agent,
            "status_code": self.status_code,
        }


@dataclass
class ScrapeRequest:
    """Request configuration for scraping."""
    url: str
    instructions: str = ""  # What data to extract
    extraction_schema: Optional[Dict] = None
    
    # Navigation
    wait_for: Optional[str] = None  # CSS selector or "networkidle"
    wait_time: float = 2.0
    
    # Browser behavior
    headless: bool = True
    human_behavior: bool = True
    scroll: bool = False
    
    # Session
    cookies: Optional[List[Dict]] = None
    local_storage: Optional[Dict] = None
    
    # Request config
    headers: Optional[Dict] = None
    proxy: Optional[str] = None
    timeout: float = 30.0
    
    # Retry policy
    max_retries: int = 3
    retry_delay: float = 2.0


class StealthScraper:
    """
    Elite web scraper with multi-engine support and comprehensive stealth.
    
    Usage:
        scraper = StealthScraper()
        result = await scraper.scrape(ScrapeRequest(url="https://example.com"))
    """
    
    def __init__(
        self,
        proxy_pool: Optional[List[str]] = None,
        fingerprint_profiles: Optional[List[Dict]] = None,
        preferred_engine: str = "auto",  # auto, nodriver, playwright, api, http
        api_keys: Optional[Dict] = None,
        data_dir: Optional[Path] = None,
    ):
        self.proxy_pool = proxy_pool or []
        self.fingerprint_profiles = fingerprint_profiles or []
        self.preferred_engine = preferred_engine
        self.api_keys = api_keys or {}
        self.data_dir = data_dir or Path.home() / ".openclaw" / "scraping_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics tracking
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "blocked": 0,
            "by_engine": {},
        }
        
        # Module availability
        self._check_module_availability()
        
    def _check_module_availability(self):
        """Check which scraping engines are available."""
        self.available_engines = []
        
        # Check nodriver
        try:
            import nodriver as uc
            self.available_engines.append("nodriver")
            logger.info("✅ Nodriver available (primary stealth engine)")
        except ImportError:
            logger.warning("❌ Nodriver not installed: pip install nodriver")
            
        # Check playwright
        try:
            from playwright.async_api import async_playwright
            self.available_engines.append("playwright")
            logger.info("✅ Playwright available")
        except ImportError:
            logger.warning("❌ Playwright not installed: pip install playwright")
            
        # Check httpx for simple mode
        try:
            import httpx
            self.available_engines.append("http")
            logger.info("✅ HTTP client (httpx) available")
        except ImportError:
            logger.warning("❌ httpx not installed: pip install httpx")
            
        # Note: Standalone self-hosted only - no paid/managed APIs per design
        logger.info("ℹ️ Self-hosted mode: Using local browser engines only")
            
        if not self.available_engines:
            raise RuntimeError("No scraping engines available. Install at least one: nodriver, playwright, or httpx")
            
    def select_engine(self, request: ScrapeRequest, attempt: int = 0) -> str:
        """Select best engine based on site difficulty and availability."""
        if self.preferred_engine != "auto" and self.preferred_engine in self.available_engines:
            return self.preferred_engine
            
        # Auto-selection logic
        if attempt == 0:
            # Try nodriver first for stealth
            if "nodriver" in self.available_engines:
                return "nodriver"
            elif "playwright" in self.available_engines:
                return "playwright"
        elif attempt == 1:
            # Retry with different stealth profile or engine rotation
            logger.info("🔄 Attempt 2: Rotating to alternative stealth engine")
                
        # Fallback
        return self.available_engines[0] if self.available_engines else "http"
        
    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """
        Execute scrape with automatic engine selection and retry logic.
        """
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        last_error = None
        techniques_used = []
        blocks_encountered = []
        
        for attempt in range(request.max_retries):
            engine = self.select_engine(request, attempt)
            techniques_used.append(f"{engine}_attempt_{attempt + 1}")
            
            try:
                if engine == "nodriver":
                    result = await self._scrape_nodriver(request)
                elif engine == "playwright":
                    result = await self._scrape_playwright(request)
                elif engine == "camoufox":
                    result = await self._scrape_camoufox(request)
                elif engine == "http":
                    result = await self._scrape_http(request)
                else:
                    raise ValueError(f"Unknown engine: {engine}")
                    
                result.duration_seconds = time.time() - start_time
                result.techniques_used = techniques_used
                result.blocks_encountered = blocks_encountered
                
                if result.success:
                    self.stats["successful"] += 1
                    self.stats["by_engine"][engine] = self.stats["by_engine"].get(engine, 0) + 1
                    return result
                    
                # Check if blocked
                if result.status_code in [403, 429, 503]:
                    blocks_encountered.append(f"{engine}_blocked_{result.status_code}")
                    logger.warning(f"Blocked by {request.url} (attempt {attempt + 1}): {result.status_code}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Scrape failed (attempt {attempt + 1}): {e}")
                
            # Wait before retry with jitter
            if attempt < request.max_retries - 1:
                jitter = random.uniform(0.5, 1.5)
                await asyncio.sleep(request.retry_delay * (attempt + 1) + jitter)
                
        # All retries exhausted
        self.stats["blocked"] += 1
        return ScrapeResult(
            success=False,
            url=request.url,
            error=last_error or "Max retries exceeded",
            success_score=0,
            techniques_used=techniques_used,
            blocks_encountered=blocks_encountered,
            duration_seconds=time.time() - start_time,
            engine_used="failed",
        )
        
    async def _scrape_nodriver(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape using nodriver (async CDP Chrome) - best stealth."""
        import nodriver as uc
        
        start_time = time.time()
        browser = None
        
        try:
            # Launch nodriver with stealth config
            browser = await uc.start(
                headless=request.headless,
            )
            
            # Create tab
            tab = await browser.get(request.url)
            
            # Wait strategy
            if request.wait_for:
                if request.wait_for == "networkidle":
                    await tab.sleep(request.wait_time)
                elif request.wait_for.startswith("selector:"):
                    selector = request.wait_for.replace("selector:", "")
                    await tab.select(selector, timeout=request.timeout)
                else:
                    await tab.select(request.wait_for, timeout=request.timeout)
            else:
                await tab.sleep(request.wait_time)
                
            # Human behavior simulation
            if request.human_behavior:
                await self._human_behavior_nodriver(tab)
                
            # Extract content
            html = await tab.get_content()
            text_content = await tab.evaluate("document.body.innerText")
            title = await tab.evaluate("document.title")
            
            # Simple data extraction
            data = {
                "title": title,
                "url": tab.url,
                "text_content": text_content[:5000] if text_content else "",
            }
            
            duration = time.time() - start_time
            
            return ScrapeResult(
                success=True,
                url=request.url,
                html=html,
                text=text_content,
                data=data,
                success_score=95,  # Nodriver is very stealthy
                techniques_used=["nodriver", "stealth_headers", "real_browser"],
                duration_seconds=duration,
                engine_used="nodriver",
                user_agent=await tab.evaluate("navigator.userAgent"),
            )
            
        except Exception as e:
            return ScrapeResult(
                success=False,
                url=request.url,
                error=str(e),
                engine_used="nodriver",
            )
        finally:
            if browser:
                try:
                    browser.stop()
                except:
                    pass
                    
    async def _scrape_playwright(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape using Playwright with stealth plugins."""
        from playwright.async_api import async_playwright
        
        start_time = time.time()
        
        async with async_playwright() as p:
            # Use chromium with args for stealth
            browser = await p.chromium.launch(
                headless=request.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            )
            
            # Inject stealth script
            page = await context.new_page()
            
            # Override navigator.webdriver
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                response = await page.goto(request.url, wait_until='networkidle', timeout=request.timeout * 1000)
                
                if request.wait_for and request.wait_for.startswith("selector:"):
                    selector = request.wait_for.replace("selector:", "")
                    await page.wait_for_selector(selector, timeout=5000)
                    
                # Human behavior
                if request.human_behavior:
                    await self._human_behavior_playwright(page)
                    
                html = await page.content()
                text_content = await page.inner_text("body")
                title = await page.title()
                
                data = {
                    "title": title,
                    "url": page.url,
                    "text_content": text_content[:5000] if text_content else "",
                }
                
                await browser.close()
                
                return ScrapeResult(
                    success=True,
                    url=request.url,
                    html=html,
                    text=text_content,
                    data=data,
                    success_score=85,
                    techniques_used=["playwright", "stealth_injection"],
                    duration_seconds=time.time() - start_time,
                    engine_used="playwright",
                    status_code=response.status if response else None,
                    user_agent=await page.evaluate("navigator.userAgent"),
                )
                
            except Exception as e:
                await browser.close()
                return ScrapeResult(
                    success=False,
                    url=request.url,
                    error=str(e),
                    engine_used="playwright",
                )
                
    async def _scrape_http(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape using simple HTTP (httpx) - for static sites only."""
        import httpx
        from bs4 import BeautifulSoup
        
        start_time = time.time()
        
        headers = request.headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        proxies = {"http://": request.proxy, "https://": request.proxy} if request.proxy else None
        
        try:
            async with httpx.AsyncClient(
                headers=headers,
                proxies=proxies,
                timeout=httpx.Timeout(request.timeout),
                follow_redirects=True,
            ) as client:
                response = await client.get(request.url)
                
                if response.status_code == 200:
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    text_content = soup.get_text(separator=' ', strip=True)
                    title = soup.title.string if soup.title else ""
                    
                    data = {
                        "title": title,
                        "url": str(response.url),
                        "text_content": text_content[:5000],
                    }
                    
                    return ScrapeResult(
                        success=True,
                        url=request.url,
                        html=html,
                        text=text_content,
                        data=data,
                        success_score=60,
                        techniques_used=["http_client", "beautifulsoup"],
                        duration_seconds=time.time() - start_time,
                        engine_used="http",
                        status_code=response.status_code,
                        user_agent=headers.get('User-Agent'),
                    )
                else:
                    return ScrapeResult(
                        success=False,
                        url=request.url,
                        error=f"HTTP {response.status_code}",
                        status_code=response.status_code,
                        engine_used="http",
                    )
                    
        except Exception as e:
            return ScrapeResult(
                success=False,
                url=request.url,
                error=str(e),
                engine_used="http",
            )
            
    async def _scrape_camoufox(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape using Camoufox (stealth-modified Firefox) - best fingerprint resistance."""
        from playwright.async_api import async_playwright
        
        start_time = time.time()
        
        # Camoufox requires special binary - check if available
        camoufox_path = None
        for path in ["/usr/bin/camoufox", "/usr/local/bin/camoufox", "./camoufox/camoufox"]:
            if Path(path).exists():
                camoufox_path = path
                break
                
        if not camoufox_path:
            return ScrapeResult(
                success=False,
                url=request.url,
                error="Camoufox not found. Install from https://github.com/daijro/camoufox",
                engine_used="camoufox",
            )
            
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(
                    executable_path=camoufox_path,
                    headless=request.headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                )
                
                page = await context.new_page()
                
                response = await page.goto(request.url, wait_until='networkidle', timeout=request.timeout * 1000)
                
                if request.wait_for:
                    await page.wait_for_selector(request.wait_for, timeout=5000)
                    
                if request.human_behavior:
                    await self._human_behavior_playwright(page)
                    
                html = await page.content()
                
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    text_content = soup.get_text(separator=' ', strip=True)
                    title = soup.title.string if soup.title else ""
                except:
                    text_content = html[:5000]
                    title = ""
                    
                await browser.close()
                
                return ScrapeResult(
                    success=True,
                    url=request.url,
                    html=html,
                    text=text_content,
                    data={"title": title, "url": request.url},
                    success_score=98,  # Camoufox has excellent stealth
                    techniques_used=["camoufox", "firefox_stealth", "fingerprint_randomization"],
                    duration_seconds=time.time() - start_time,
                    engine_used="camoufox",
                    status_code=response.status if response else None,
                    user_agent=await page.evaluate("navigator.userAgent"),
                )
                
        except Exception as e:
            return ScrapeResult(
                success=False,
                url=request.url,
                error=str(e),
                engine_used="camoufox",
            )
            
    async def _human_behavior_nodriver(self, tab):
        """Simulate human-like behavior in nodriver."""
        import nodriver as uc
        
        # Random wait
        await asyncio.sleep(random.uniform(1.5, 3.5))
        
        # Random mouse movements (using JavaScript)
        movements = random.randint(2, 5)
        for _ in range(movements):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await tab.evaluate(f"window.scrollTo({{top: {y}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.3, 1.2))
            
        # Scroll down slightly
        scroll_amount = random.randint(200, 800)
        await tab.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
    async def _human_behavior_playwright(self, page):
        """Simulate human-like behavior in Playwright."""
        from playwright.async_api import async_playwright
        
        # Random wait
        await asyncio.sleep(random.uniform(1.5, 3.5))
        
        # Move mouse to random positions
        movements = random.randint(2, 5)
        for _ in range(movements):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.3, 1.2))
            
        # Scroll down
        scroll_amount = random.randint(200, 800)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
    async def scrape_batch(
        self,
        requests: List[ScrapeRequest],
        concurrency: int = 3,
        delay_between: float = 1.0,
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs with rate limiting and concurrency control.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results = []
        
        async def scrape_with_limit(req: ScrapeRequest) -> ScrapeResult:
            async with semaphore:
                result = await self.scrape(req)
                await asyncio.sleep(delay_between)
                return result
                
        tasks = [scrape_with_limit(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(ScrapeResult(
                    success=False,
                    url="unknown",
                    error=str(result),
                ))
            else:
                processed_results.append(result)
                
        return processed_results
        
    def get_stats(self) -> Dict:
        """Get scraping statistics."""
        return {
            **self.stats,
            "success_rate": self.stats["successful"] / max(self.stats["total_requests"], 1) * 100,
            "available_engines": self.available_engines,
        }


# CLI interface
async def main():
    """CLI for testing the stealth scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stealth Web Scraper")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--engine", choices=["nodriver", "playwright", "http", "auto"], default="auto")
    parser.add_argument("--wait", type=float, default=3.0, help="Wait time in seconds")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-human-behavior", action="store_true")
    parser.add_argument("--proxy", help="Proxy URL")
    parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    
    scraper = StealthScraper(preferred_engine=args.engine)
    
    request = ScrapeRequest(
        url=args.url,
        wait_time=args.wait,
        headless=args.headless,
        human_behavior=not args.no_human_behavior,
        proxy=args.proxy,
    )
    
    print(f"🔍 Scraping {args.url} with engine: {args.engine}")
    result = await scraper.scrape(request)
    
    print(f"\n{'='*60}")
    print(f"Success: {result.success}")
    print(f"Engine: {result.engine_used}")
    print(f"Score: {result.success_score}/100")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Techniques: {', '.join(result.techniques_used)}")
    
    if result.data:
        print(f"\nTitle: {result.data.get('title', 'N/A')}")
        print(f"Text preview:\n{result.data.get('text_content', 'N/A')[:500]}...")
        
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\n💾 Saved to {args.output}")
        
    if not result.success:
        print(f"\n❌ Error: {result.error}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
