#!/usr/bin/env python3
"""
Fingerprint Manager - Browser Identity & Stealth Configuration

Generates realistic, consistent browser fingerprints per session.
Handles User-Agent rotation, header consistency, viewport, timezone,
WebGL spoofing, canvas noise, and all anti-fingerprinting techniques.
"""

import random
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint profile for stealth consistency."""
    
    # Identity
    user_agent: str
    accept_language: str
    platform: str
    
    # Viewport & Screen
    viewport_width: int
    viewport_height: int
    screen_width: int
    screen_height: int
    device_pixel_ratio: float
    color_depth: int
    
    # Hardware
    hardware_concurrency: int
    device_memory: int  # GB
    
    # Time & Locale
    timezone: str
    locale: str
    
    # WebGL / Graphics
    vendor: str
    renderer: str
    webgl_noise: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # Canvas fingerprint noise (consistent within session)
    canvas_seed: int = field(default_factory=lambda: random.randint(10000, 99999))
    
    # Audio fingerprint
    audio_seed: int = field(default_factory=lambda: random.randint(10000, 99999))
    
    # Headers
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str
    
    # Plugins & Features
    pdf_viewer_enabled: bool = True
    plugins: List[Dict] = field(default_factory=list)
    
    # TLS/JA3 (for HTTP clients)
    tls_fingerprint: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
        
    def to_playwright_context(self) -> Dict[str, Any]:
        """Convert to Playwright browser context options."""
        return {
            "user_agent": self.user_agent,
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "screen": {
                "width": self.screen_width,
                "height": self.screen_height,
            },
            "device_scale_factor": self.device_pixel_ratio,
            "locale": self.locale,
            "timezone_id": self.timezone,
            "extra_http_headers": {
                "Accept-Language": self.accept_language,
                "Sec-CH-UA": self.sec_ch_ua,
                "Sec-CH-UA-Mobile": self.sec_ch_ua_mobile,
                "Sec-CH-UA-Platform": self.sec_ch_ua_platform,
            }
        }


class FingerprintManager:
    """
    Generates and manages realistic browser fingerprints for stealth.
    
    Usage:
        manager = FingerprintManager()
        fp = manager.generate_fingerprint()
        context_options = fp.to_playwright_context()
    """
    
    # Realistic browser data - updated 2025
    DESKTOP_USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    ]
    
    MOBILE_USER_AGENTS = [
        # Chrome Android
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.0.0 Mobile/15E148 Safari/604.1",
        # Safari iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    ]
    
    VIEWPORT_PRESETS = [
        {"width": 1920, "height": 1080, "dpr": 1.0},  # FHD
        {"width": 1366, "height": 768, "dpr": 1.0},   # Laptop
        {"width": 1440, "height": 900, "dpr": 1.0},    # Mac
        {"width": 1280, "height": 720, "dpr": 1.0},    # Small laptop
        {"width": 1536, "height": 864, "dpr": 1.25},   # Windows laptop
        {"width": 2560, "height": 1440, "dpr": 1.0},  # QHD
    ]
    
    TIMEZONES = [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Berlin",
        "Europe/Paris",
        "Asia/Tokyo",
        "Asia/Singapore",
        "Australia/Sydney",
    ]
    
    GRAPHICS_VENDORS = [
        "Intel Inc.",
        "Google Inc. (NVIDIA)",
        "Google Inc. (AMD)",
        "Apple Inc.",
    ]
    
    GRAPHICS_RENDERERS = [
        "Intel Iris Xe Graphics",
        "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Apple M1 GPU",
        "Apple M2 GPU",
        "Apple M3 GPU",
    ]
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".openclaw" / "fingerprints"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._profile_cache: Dict[str, BrowserFingerprint] = {}
        
    def generate_fingerprint(
        self,
        mobile: bool = False,
        os_hint: Optional[str] = None,
        locale_hint: Optional[str] = None,
    ) -> BrowserFingerprint:
        """Generate a complete, internally consistent browser fingerprint."""
        
        # Select user agent
        if mobile:
            ua = random.choice(self.MOBILE_USER_AGENTS)
        else:
            ua_pool = [u for u in self.DESKTOP_USER_AGENTS 
                      if (os_hint is None or os_hint.lower() in u.lower())]
            ua = random.choice(ua_pool) if ua_pool else random.choice(self.DESKTOP_USER_AGENTS)
            
        # Parse platform from UA
        if "Windows" in ua:
            platform = "Win32"
            os_name = "Windows"
        elif "Mac" in ua:
            platform = "MacIntel"
            os_name = "macOS"
        elif "Linux" in ua:
            platform = "Linux x86_64"
            os_name = "Linux"
        else:
            platform = "Win32"
            os_name = "Windows"
            
        # Viewport (related to OS)
        viewport = random.choice(self.VIEWPORT_PRESETS)
        if os_name == "macOS":
            viewport = {"width": 1440, "height": 900, "dpr": 2.0}
            
        # Locale and timezone
        locale = locale_hint or "en-US"
        timezone = random.choice(self.TIMEZONES)
        
        # Sec-CH-UA headers (Chrome only)
        if "Chrome" in ua:
            chrome_version = ua.split("Chrome/")[1].split(" ")[0] if "Chrome/" in ua else "126.0.0.0"
            major_version = chrome_version.split(".")[0]
            sec_ch_ua = f'"Not.A/Brand";v="8", "Chromium";v="{major_version}", "Google Chrome";v="{major_version}"'
            sec_ch_ua_mobile = "?0" if not mobile else "?1"
            sec_ch_ua_platform = f'"{os_name}"'
        else:
            sec_ch_ua = ''
            sec_ch_ua_mobile = "?0"
            sec_ch_ua_platform = f'"{os_name}"'
            
        # Hardware specs
        hw_concurrency = random.choice([4, 6, 8, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])
        
        # Graphics
        vendor = random.choice(self.GRAPHICS_VENDORS)
        renderer = random.choice(self.GRAPHICS_RENDERERS)
        
        # WebGL noise (consistent within session)
        webgl_noise = [
            random.uniform(-0.0001, 0.0001),
            random.uniform(-0.0001, 0.0001),
            random.uniform(-0.0001, 0.0001),
        ]
        
        # Build fingerprint
        fp = BrowserFingerprint(
            user_agent=ua,
            accept_language=f"{locale},en;q=0.9",
            platform=platform,
            viewport_width=viewport["width"],
            viewport_height=viewport["height"],
            screen_width=viewport["width"],
            screen_height=viewport["height"],
            device_pixel_ratio=viewport["dpr"],
            color_depth=24,
            hardware_concurrency=hw_concurrency,
            device_memory=device_memory,
            timezone=timezone,
            locale=locale,
            vendor=vendor,
            renderer=renderer,
            webgl_noise=webgl_noise,
            canvas_seed=random.randint(10000, 99999),
            audio_seed=random.randint(10000, 99999),
            sec_ch_ua=sec_ch_ua,
            sec_ch_ua_mobile=sec_ch_ua_mobile,
            sec_ch_ua_platform=sec_ch_ua_platform,
            pdf_viewer_enabled=True,
            plugins=[
                {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer"},
                {"name": "Native Client", "filename": "internal-nacl-plugin"},
            ] if "Chrome" in ua else [],
        )
        
        return fp
        
    def get_stealth_js(self, fp: BrowserFingerprint) -> str:
        """Generate JavaScript to inject for stealth (webdriver patching, etc.)."""
        
        js = f"""
        // Stealth patches - consistent with fingerprint
        (() => {{
            'use strict';
            
            // Remove webdriver property
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {JSON.dumps(fp.plugins)},
            }});
            
            // Hardware specs
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fp.hardware_concurrency},
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fp.device_memory},
            }});
            
            // Canvas fingerprinting protection with consistent noise
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            const canvasNoise = {fp.canvas_seed} / 100000;
            
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                if (this.width > 16 && this.height > 16) {{
                    // Add subtle noise to larger canvases
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = (imageData.data[i] + canvasNoise) % 256;
                        }}
                        ctx.putImageData(imageData, 0, 0);
                    }}
                }}
                return originalToDataURL.apply(this, args);
            }};
            
            // WebGL vendor/renderer spoofing
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return "{fp.vendor}";
                }}
                if (parameter === 37446) {{
                    return "{fp.renderer}";
                }}
                return getParameter.apply(this, arguments);
            }};
            
            // Notification permission spoofing (default: prompt)
            const originalNotification = window.Notification;
            Object.defineProperty(Notification, 'permission', {{
                get: () => "default",
            }});
            
            // Permissions API spoofing
            if (navigator.permissions) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    return originalQuery.apply(this, [parameters])
                        .then((result) => {{
                            if (parameters.name === 'notifications') {{
                                Object.defineProperty(result, 'state', {{
                                    get: () => "prompt",
                                }});
                            }}
                            return result;
                        }});
                }};
            }}
            
            // PluginArray spoofing
            class FakePluginArray {{
                constructor() {{
                    this.length = {len(fp.plugins)};
                    this.item = (idx) => {JSON.dumps(fp.plugins)}[idx] || null;
                    this.namedItem = (name) => {JSON.dumps(fp.plugins)}.find(p => p.name === name) || null;
                }}
            }}
            
            // Chrome runtime detection prevention
            Object.defineProperty(window, 'chrome', {{
                get: () => {{
                    if (!window.__chrome) {{
                        window.__chrome = {{}};
                    }}
                    return window.__chrome;
                }},
            }});
            
            // Hide automation indicators
            Object.defineProperty(document, 'documentElement', {{
                get: () => {{
                    const html = document.getElementsByTagName('html')[0];
                    if (html) html.removeAttribute('webdriver');
                    return html;
                }},
            }});
            
        }})();
        """
        return js
        
    def get_full_header_set(self, fp: BrowserFingerprint) -> Dict[str, str]:
        """Get complete, consistent HTTP headers for requests."""
        headers = {
            "User-Agent": fp.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": fp.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        }
        
        if "Chrome" in fp.user_agent:
            headers["Sec-CH-UA"] = fp.sec_ch_ua
            headers["Sec-CH-UA-Mobile"] = fp.sec_ch_ua_mobile
            headers["Sec-CH-UA-Platform"] = fp.sec_ch_ua_platform
            
        return headers
        
    def save_profile(self, fp: BrowserFingerprint, name: str):
        """Save a fingerprint profile for reuse."""
        profile_path = self.data_dir / f"{name}.json"
        with open(profile_path, 'w') as f:
            json.dump(fp.to_dict(), f, indent=2)
        logger.info(f"Profile saved: {name}")
        
    def load_profile(self, name: str) -> Optional[BrowserFingerprint]:
        """Load a saved fingerprint profile."""
        if name in self._profile_cache:
            return self._profile_cache[name]
            
        profile_path = self.data_dir / f"{name}.json"
        if profile_path.exists():
            with open(profile_path) as f:
                data = json.load(f)
            fp = BrowserFingerprint(**data)
            self._profile_cache[name] = fp
            return fp
        return None


# Standalone test
if __name__ == "__main__":
    import sys
    
    manager = FingerprintManager()
    fp = manager.generate_fingerprint()
    
    print("=" * 60)
    print("Browser Fingerprint Generated")
    print("=" * 60)
    
    for key, value in fp.to_dict().items():
        if key in ['user_agent', 'sec_ch_ua']:
            print(f"{key}: {value[:70]}...")
        else:
            print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("Stealth JS Injection (preview):")
    print("=" * 60)
    stealth_js = manager.get_stealth_js(fp)
    print(stealth_js[:1500] + "...")
