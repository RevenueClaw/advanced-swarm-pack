#!/usr/bin/env python3
"""
Proxy Rotator - IP & Session Management

Manages proxy rotation, health checks, geolocation matching,
and intelligent routing based on target site and success rates.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Proxy configuration with health tracking."""
    url: str
    protocol: str = "http"  # http, https, socks4, socks5
    ip: str = ""
    port: int = 0
    country: str = ""
    city: str = ""
    isp: str = ""
    
    # Health metrics
    success_count: int = 0
    fail_count: int = 0
    last_used: float = 0.0
    last_checked: float = 0.0
    avg_response_time: float = 0.0
    is_banned: bool = False
    
    # Session Persistence
    sticky_session: bool = False
    session_id: str = ""
    
    def __post_init__(self):
        if not self.ip and self.url:
            # Parse proxy URL
            try:
                # Handle various formats
                if "@" in self.url:
                    # user:pass@ip:port
                    self.url = f"{self.protocol}://{self.url}"
                elif not self.url.startswith(("http://", "https://", "socks4://", "socks5://")):
                    self.url = f"{self.protocol}://{self.url}"
                    
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                self.ip = parsed.hostname
                self.port = parsed.port or (8080 if self.protocol == "http" else 1080)
            except:
                pass
                
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.5  # Unknown = 50%
        
    @property
    def is_healthy(self) -> bool:
        return not self.is_banned and self.success_rate > 0.3
        
    def record_success(self, response_time: float):
        self.success_count += 1
        self.last_used = time.time()
        # Running average
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = 0.8 * self.avg_response_time + 0.2 * response_time
            
    def record_failure(self, error_type: str = "unknown"):
        self.fail_count += 1
        self.last_used = time.time()
        
        # Auto-ban on repeated failures
        if self.fail_count >= 10 and self.success_rate < 0.1:
            self.is_banned = True
            logger.warning(f"Proxy {self.ip} auto-banned due to low success rate")


class ProxyRotator:
    """
    Intelligent proxy rotation with health tracking and site-specific routing.
    
    Usage:
        rotor = ProxyRotator()
        rotor.add_proxies_from_file("proxies.txt")
        
        proxy = rotor.get_proxy(target_url="https://example.com")
        # Use proxy...
        rotor.mark_success(proxy)
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        rotation_strategy: str = "weighted",  # round_robin, weighted, least_recent
        max_failures: int = 5,
        cooldown_seconds: float = 300.0,
    ):
        self.proxies: List[Proxy] = []
        self.data_dir = data_dir or Path.home() / ".openclaw" / "proxies"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.rotation_strategy = rotation_strategy
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        
        self._round_robin_index = 0
        self._site_proxy_map: Dict[str, Proxy] = {}  # Sticky sessions
        
        # Load persisted proxy states
        self._load_state()
        
    def add_proxy(self, proxy: Proxy):
        """Add a single proxy."""
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.ip}:{proxy.port} ({proxy.country})")
        
    def add_proxies_from_file(self, filepath: Path | str):
        """Load proxies from file (one per line, format: ip:port or protocol://ip:port)."""
        filepath = Path(filepath)
        if not filepath.exists():
            logger.error(f"Proxy file not found: {filepath}")
            return
            
        count = 0
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                try:
                    # Parse various formats
                    if '://' in line:
                        protocol, rest = line.split('://', 1)
                        proxy = Proxy(url=rest, protocol=protocol)
                    else:
                        proxy = Proxy(url=line, protocol="http")
                    
                    self.add_proxy(proxy)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse proxy line: {line} - {e}")
                    
        logger.info(f"Loaded {count} proxies from {filepath}")
        
    def add_proxies_from_json(self, filepath: Path | str):
        """Load proxies from JSON file with detailed metadata."""
        filepath = Path(filepath)
        if not filepath.exists():
            return
            
        with open(filepath) as f:
            data = json.load(f)
            
        for entry in data.get('proxies', []):
            proxy = Proxy(
                url=entry.get('url', f"http://{entry['ip']}:{entry['port']}"),
                protocol=entry.get('protocol', 'http'),
                ip=entry.get('ip'),
                port=entry.get('port'),
                country=entry.get('country', ''),
                city=entry.get('city', ''),
                isp=entry.get('isp', ''),
            )
            self.add_proxy(proxy)
            
    def get_proxy(
        self,
        target_url: Optional[str] = None,
        country_hint: Optional[str] = None,
        sticky: bool = False,
    ) -> Optional[Proxy]:
        """
        Get best proxy based on strategy and health.
        
        Args:
            target_url: URL being scraped (for sticky sessions)
            country_hint: Preferred country code (e.g., 'US', 'GB')
            sticky: Use same proxy for same target
        """
        if sticky and target_url and target_url in self._site_proxy_map:
            existing = self._site_proxy_map[target_url]
            if existing.is_healthy:
                return existing
            
        # Filter healthy proxies
        candidates = [p for p in self.proxies if p.is_healthy]
        
        # Country filter
        if country_hint:
            country_matches = [p for p in candidates if p.country.upper() == country_hint.upper()]
            if country_matches:
                candidates = country_matches
                
        if not candidates:
            # Fallback to any proxy (even unhealthy) if none available
            candidates = self.proxies
            if not candidates:
                return None
                
        # Apply rotation strategy
        if self.rotation_strategy == "round_robin":
            proxy = candidates[self._round_robin_index % len(candidates)]
            self._round_robin_index += 1
            
        elif self.rotation_strategy == "weighted":
            # Weight by success rate and response time
            weights = []
            for p in candidates:
                weight = p.success_rate / (p.avg_response_time + 0.1)
                weights.append(weight)
            proxy = random.choices(candidates, weights=weights, k=1)[0]
            
        elif self.rotation_strategy == "least_recent":
            proxy = min(candidates, key=lambda p: p.last_used)
            
        else:
            proxy = random.choice(candidates)
            
        # Store sticky session
        if sticky and target_url:
            self._site_proxy_map[target_url] = proxy
            
        return proxy
        
    def mark_success(self, proxy: Proxy, response_time: float = 0.0):
        """Record successful request."""
        proxy.record_success(response_time)
        self._save_state()
        
    def mark_failure(self, proxy: Proxy, error_type: str = "unknown"):
        """Record failed request."""
        proxy.record_failure(error_type)
        self._save_state()
        
    async def health_check(
        self,
        test_url: str = "https://httpbin.org/ip",
        timeout: float = 10.0,
    ) -> Dict[Proxy, bool]:
        """Check all proxies' health by making requests."""
        import httpx
        
        results = {}
        
        async def check_single(proxy: Proxy) -> bool:
            try:
                async with httpx.AsyncClient(
                    proxies={"http://": proxy.url, "https://": proxy.url},
                    timeout=timeout,
                ) as client:
                    start = time.time()
                    response = await client.get(test_url)
                    elapsed = time.time() - start
                    
                    if response.status_code == 200:
                        proxy.record_success(elapsed)
                        return True
                    else:
                        proxy.record_failure("bad_status")
                        return False
            except Exception as e:
                proxy.record_failure(str(type(e).__name__))
                return False
                
        tasks = [check_single(p) for p in self.proxies]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for proxy, result in zip(self.proxies, results_list):
            if isinstance(result, Exception):
                results[proxy] = False
            else:
                results[proxy] = result
                
        healthy_count = sum(1 for r in results.values() if r)
        logger.info(f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy")
        
        self._save_state()
        return results
        
    def _save_state(self):
        """Persist proxy states to disk."""
        state_file = self.data_dir / "proxy_state.json"
        state = {
            "proxies": [
                {
                    "url": p.url,
                    "success_count": p.success_count,
                    "fail_count": p.fail_count,
                    "last_used": p.last_used,
                    "avg_response_time": p.avg_response_time,
                    "is_banned": p.is_banned,
                }
                for p in self.proxies
            ]
        }
        with open(state_file, 'w') as f:
            json.dump(state, f)
            
    def _load_state(self):
        """Load persisted proxy states."""
        state_file = self.data_dir / "proxy_state.json"
        if not state_file.exists():
            return
            
        try:
            with open(state_file) as f:
                state = json.load(f)
                
            # Match by URL
            by_url = {p.url: p for p in self.proxies}
            for entry in state.get("proxies", []):
                if entry["url"] in by_url:
                    p = by_url[entry["url"]]
                    p.success_count = entry.get("success_count", 0)
                    p.fail_count = entry.get("fail_count", 0)
                    p.avg_response_time = entry.get("avg_response_time", 0)
                    p.is_banned = entry.get("is_banned", False)
        except Exception as e:
            logger.warning(f"Failed to load proxy state: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        healthy = sum(1 for p in self.proxies if p.is_healthy)
        banned = sum(1 for p in self.proxies if p.is_banned)
        
        return {
            "total": len(self.proxies),
            "healthy": healthy,
            "banned": banned,
            "avg_success_rate": sum(p.success_rate for p in self.proxies) / len(self.proxies) if self.proxies else 0,
            "countries": list(set(p.country for p in self.proxies if p.country)),
        }


# Utility: Fetch free proxy lists (USE WITH CAUTION - often unreliable)
async def fetch_free_proxies() -> List[Proxy]:
    """
    Fetch free proxies from public lists.
    WARNING: Free proxies are often slow, unreliable, and may be monitored.
    """
    proxies = []
    
    try:
        import httpx
        
        # Proxy-list.download API
        async with httpx.AsyncClient() as client:
            # HTTPS proxies
            response = await client.get(
                "https://www.proxy-list.download/api/v1/get?type=https&anon=elite",
                timeout=10.0
            )
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    if ':' in line:
                        ip, port = line.strip().split(':')
                        proxies.append(Proxy(url=f"http://{ip}:{port}", protocol="http"))
    except Exception as e:
        logger.warning(f"Failed to fetch free proxies: {e}")
        
    return proxies


if __name__ == "__main__":
    import sys
    
    rotor = ProxyRotator()
    
    # Demo with mock proxies
    test_proxies = [
        "103.149.162.194:80",
        "49.0.2.242:8090",
        "195.154.84.23:3128",
    ]
    
    for p in test_proxies:
        rotor.add_proxy(Proxy(url=p))
        
    print("Proxy Pool Statistics:")
    print(json.dumps(rotor.get_stats(), indent=2))
    
    print("\nGetting a proxy:")
    proxy = rotor.get_proxy()
    if proxy:
        print(f"  Selected: {proxy}")
