#!/usr/bin/env python3
"""
Price Tracker v1 - Advanced Swarm Pack
Tracks product prices from Amazon and other retailers with alert notifications.

Integrates with: amazon_creators_api_v1
Storage: SQLite (local, private)
Security: Credentials loaded from secure storage only
"""

import os
import re
import json
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict

# Add amazon_creators_api_v1 to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "amazon_creators_api_v1"))

try:
    from amazon_creators_api_v1 import AmazonCreatorsAPI
except ImportError:
    AmazonCreatorsAPI = None
    print("Warning: amazon_creators_api_v1 not available")


# Configuration
DEFAULT_CONFIG = {
    "db_path": Path.home() / ".openclaw" / "price_tracker.db",
    "check_interval_hours": 6,
    "price_drop_threshold_percent": 5.0,
    "max_products": 500,
}


@dataclass
class TrackedProduct:
    """Product tracking data container."""
    id: str
    query: str  # Original query (ASIN/URL/search)
    vendor: str
    asin: Optional[str]
    title: Optional[str]
    current_price: Optional[float]
    currency: str
    target_price: Optional[float]
    lowest_price: Optional[float]
    highest_price: Optional[float]
    affiliate_link: Optional[str]
    image_url: Optional[str]
    last_checked: Optional[str]
    created_at: str
    status: str  # active, paused, error


class PriceTracker:
    """
    Price tracking system with Amazon Creators API integration.
    
    Features:
    - SQLite storage for price history
    - Multi-vendor support (Amazon primary)
    - Smart ASIN/URL parsing
    - Price drop alerts
    - Affiliate link generation
    """
    
    def __init__(self, db_path: Optional[Path] = None, partner_tag: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.config["db_path"] = db_path or self.config["db_path"]
        self.db_path = Path(self.config["db_path"])
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Amazon API if available
        self.amazon_api = None
        if AmazonCreatorsAPI and partner_tag:
            try:
                self.amazon_api = AmazonCreatorsAPI(partner_tag=partner_tag)
            except Exception as e:
                print(f"Warning: Could not initialize Amazon API: {e}")
        elif AmazonCreatorsAPI:
            try:
                self.amazon_api = AmazonCreatorsAPI()
            except Exception as e:
                print(f"Warning: Could not initialize Amazon API: {e}")
        
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    vendor TEXT NOT NULL DEFAULT 'amazon',
                    asin TEXT,
                    title TEXT,
                    current_price REAL,
                    currency TEXT DEFAULT 'USD',
                    target_price REAL,
                    lowest_price REAL,
                    highest_price REAL,
                    affiliate_link TEXT,
                    image_url TEXT,
                    last_checked TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                );
                
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    price REAL,
                    currency TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_product_id ON price_history(product_id);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON price_history(timestamp);
            """)
    
    def _generate_id(self, query: str, vendor: str) -> str:
        """Generate unique ID from query and vendor."""
        import hashlib
        return hashlib.md5(f"{vendor}:{query}".encode()).hexdigest()[:16]
    
    def _extract_asin(self, query: str) -> Optional[str]:
        """Try to extract ASIN from query or URL."""
        # Direct ASIN pattern (10 alphanumeric, starts with B)
        if re.match(r'^[Bb][A-Za-z0-9]{9}$', query.strip()):
            return query.strip().upper()
        
        # URL patterns
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'ASIN=([A-Z0-9]{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None
    
    def _rate_limit_sleep(self, vendor: str):
        """Rate limiting between requests."""
        time.sleep(1.2)  # Conservative: ~50 requests/min max
    
    def add_product(
        self,
        query_or_asin: str,
        target_price: Optional[float] = None,
        vendor: str = "amazon"
    ) -> Dict:
        """
        Add a product to tracking.
        
        Args:
            query_or_asin: ASIN, Amazon URL, or search term
            target_price: Alert threshold price
            vendor: 'amazon', 'microcenter', 'pihut', etc.
        
        Returns:
            Product info dict with tracking ID
        """
        product_id = self._generate_id(query_or_asin, vendor)
        
        # Check if already tracking
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            
            if existing:
                return {"success": False, "error": "Already tracking this product", "id": product_id}
        
        # Extract ASIN if possible
        asin = self._extract_asin(query_or_asin) if vendor == "amazon" else None
        
        # Insert initial record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO products 
                (id, query, vendor, asin, target_price, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
            """, (product_id, query_or_asin, vendor, asin, target_price, 
                  datetime.now().isoformat()))
        
        # Fetch initial price data
        result = self.get_current_price(product_id)
        
        return {
            "success": True,
            "id": product_id,
            "query": query_or_asin,
            "vendor": vendor,
            "asin": asin,
            "initial_check": result
        }
    
    def _fetch_amazon_data(self, product: Dict) -> Dict:
        """
        Fetch product data via Amazon Creators API or fallback.
        Improved to automatically retry with web scraping if API returns None price.
        """
        if not self.amazon_api:
            return {"error": "Amazon API not available"}
        
        result = None
        
        try:
            # Try ASIN lookup first
            if product.get("asin"):
                result = self.amazon_api.get_item(product["asin"])
            else:
                # Fallback to search
                results = self.amazon_api.search_items(
                    product["query"],
                    search_index="All",
                    item_count=1
                )
                if results:
                    result = results[0]
                    result["source"] = "creators_api_search"
            
            # Check if we got valid data
            if result:
                # If price is None but we have an ASIN -> try scraping
                if result.get("price") is None and product.get("asin"):
                    print(f"  API returned no price for {product['asin']}, trying web scrape fallback...")
                    scrape_result = self._scrape_amazon(product)
                    if scrape_result and scrape_result.get("price"):
                        # Merge: use API data + scraped price
                        return {
                            "title": result.get("title") if result.get("title") else scrape_result.get("title"),
                            "price": scrape_result.get("price"),
                            "currency": scrape_result.get("currency", "USD"),
                            "affiliate_link": result.get("affiliate_link", scrape_result.get("affiliate_link")),
                            "image_url": result.get("images", {}).get("primary", {}).get("large", {}).get("URL") or scrape_result.get("image_url"),
                            "source": "api+scrape"
                        }
                
                # Return API result (with or without price)
                return {
                    "title": result.get("title"),
                    "price": result.get("price"),
                    "currency": result.get("currency", "USD"),
                    "affiliate_link": result.get("affiliate_link"),
                    "image_url": result.get("images", {}).get("primary", {}).get("large", {}).get("URL"),
                    "is_buy_box_winner": result.get("is_buy_box_winner"),
                    "availability": result.get("availability"),
                    "source": result.get("source", "creators_api")
                }
            
            return {"error": "No results from Amazon API"}
            
        except Exception as e:
            print(f"  API exception: {e}, trying web scrape fallback...")
            # Fallback to web scraping
            return self._scrape_amazon(product)
    
    def _scrape_amazon(self, product: Dict) -> Dict:
        """Fallback: Scrape Amazon product page."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {"error": "beautifulsoup4 not installed for scraping"}
        
        asin = product.get("asin")
        if not asin:
            return {"error": "Cannot scrape without ASIN"}
        
        url = f"https://www.amazon.com/dp/{asin}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Title
            title_elem = soup.find("span", {"id": "productTitle"})
            title = title_elem.text.strip() if title_elem else None
            
            # Price (try multiple selectors)
            price = None
            for selector in ["span.a-price-whole", "span.a-offscreen"]:
                elem = soup.select_one(selector)
                if elem:
                    import re
                    match = re.search(r'[\d,.]+', elem.text.replace(',', ''))
                    if match:
                        price = float(match.group())
                        break
            
            # Image
            img = soup.find("img", {"id": "landingImage"})
            image_url = img.get("src") if img else None
            
            return {
                "title": title,
                "price": price,
                "currency": "USD",
                "affiliate_link": f"https://www.amazon.com/dp/{asin}?tag={os.getenv('AMAZON_PARTNER_TAG', 'vhicklegar011-20')}",
                "image_url": image_url,
                "source": "web_scrape"
            }
        except Exception as e:
            return {"error": f"Scraping failed: {e}"}
    
    def get_current_price(self, product_id: str) -> Dict:
        """Fetch current price for a tracked product."""
        with sqlite3.connect(self.db_path) as conn:
            product = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            
            if not product:
                return {"error": "Product not found"}
            
            product_dict = {
                "id": product[0],
                "query": product[1],
                "vendor": product[2],
                "asin": product[3],
            }
        
        # Fetch based on vendor
        if product_dict["vendor"] == "amazon":
            data = self._fetch_amazon_data(product_dict)
        else:
            data = {"error": f"Vendor {product_dict['vendor']} not yet implemented"}
        
        if "error" in data:
            return {"success": False, "error": data["error"], "id": product_id}
        
        # Update database
        now = datetime.now().isoformat()
        price = data.get("price")
        
        with sqlite3.connect(self.db_path) as conn:
            # Get current price history for min/max
            history = conn.execute(
                "SELECT MIN(price), MAX(price) FROM price_history WHERE product_id = ?",
                (product_id,)
            ).fetchone()
            
            lowest = history[0] if history[0] else price
            highest = history[1] if history[1] else price
            
            if price:
                lowest = min(lowest, price) if lowest else price
                highest = max(highest, price) if highest else price
            
            conn.execute("""
                UPDATE products SET
                    title = ?,
                    current_price = ?,
                    currency = ?,
                    lowest_price = ?,
                    highest_price = ?,
                    affiliate_link = ?,
                    image_url = ?,
                    last_checked = ?
                WHERE id = ?
            """, (
                data.get("title"),
                price,
                data.get("currency", "USD"),
                lowest,
                highest,
                data.get("affiliate_link"),
                data.get("image_url"),
                now,
                product_id
            ))
            
            # Add to history
            if price:
                conn.execute(
                    "INSERT INTO price_history (product_id, price, currency) VALUES (?, ?, ?)",
                    (product_id, price, data.get("currency", "USD"))
                )
        
        return {
            "success": True,
            "id": product_id,
            "title": data.get("title"),
            "price": price,
            "currency": data.get("currency"),
            "affiliate_link": data.get("affiliate_link"),
            "source": data.get("source"),
            "timestamp": now
        }
    
    def check_all_prices(self) -> Dict:
        """
        Check prices for all active products.
        
        Returns:
            Dict with price_drops and full status
        """
        with sqlite3.connect(self.db_path) as conn:
            products = conn.execute(
                "SELECT id, query, current_price, target_price FROM products WHERE status = 'active'"
            ).fetchall()
        
        results = {
            "checked": 0,
            "price_drops": [],
            "errors": [],
            "status": []
        }
        
        for product in products:
            product_id, query, old_price, target = product
            
            result = self.get_current_price(product_id)
            results["checked"] += 1
            
            if not result.get("success"):
                results["errors"].append({
                    "id": product_id,
                    "query": query,
                    "error": result.get("error")
                })
                continue
            
            new_price = result.get("price")
            
            # Check for price drop
            if old_price and new_price and new_price < old_price:
                drop_pct = ((old_price - new_price) / old_price) * 100
                
                results["price_drops"].append({
                    "id": product_id,
                    "query": query,
                    "old_price": old_price,
                    "new_price": new_price,
                    "drop_percent": round(drop_pct, 2),
                    "affiliate_link": result.get("affiliate_link")
                })
            
            # Check if below target
            if target and new_price and new_price <= target:
                results["status"].append({
                    "id": product_id,
                    "query": query,
                    "status": "target_reached",
                    "current_price": new_price,
                    "target_price": target
                })
            
            self._rate_limit_sleep("amazon")
        
        return results
    
    def generate_alert_report(self) -> str:
        """Generate formatted alert report with affiliate links."""
        results = self.check_all_prices()
        
        lines = [
            "=" * 70,
            "PRICE TRACKER ALERT REPORT",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Products Checked: {results['checked']}",
            ""
        ]
        
        if results["price_drops"]:
            lines.append("🟢 PRICE DROPS DETECTED")
            lines.append("-" * 70)
            for drop in results["price_drops"]:
                lines.append(f"📉 {drop['query'][:50]}")
                lines.append(f"   ${drop['old_price']:.2f} → ${drop['new_price']:.2f} ({drop['drop_percent']}% off)")
                lines.append(f"   Link: {drop['affiliate_link']}")
                lines.append("")
            lines.append("")
        
        if results["status"]:
            lines.append("🎯 TARGET PRICE REACHED")
            lines.append("-" * 70)
            for status in results["status"]:
                lines.append(f"✅ {status['query'][:50]}")
                lines.append(f"   Current: ${status['current_price']:.2f} (Target: ${status['target_price']:.2f})")
                lines.append("")
            lines.append("")
        
        if not results["price_drops"] and not results["status"]:
            lines.append("📊 No price changes detected")
            lines.append("")
        
        if results["errors"]:
            lines.append(f"⚠️  {len(results['errors'])} products failed to check")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\\n".join(lines)
    
    def get_price_history(self, product_id: str, limit: int = 100) -> List[Dict]:
        """
        Get price history for a product.
        
        Args:
            product_id: Product tracking ID
            limit: Max history entries
        
        Returns:
            List of price history entries
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT price, currency, timestamp 
                FROM price_history 
                WHERE product_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (product_id, limit)).fetchall()
        
        return [
            {
                "price": row[0],
                "currency": row[1],
                "timestamp": row[2]
            }
            for row in rows
        ]
    
    def list_products(self, status: str = "all") -> List[Dict]:
        """
        List all tracked products.
        
        Args:
            status: 'all', 'active', 'paused', 'error'
        """
        query = "SELECT * FROM products"
        params = ()
        
        if status != "all":
            query += " WHERE status = ?"
            params = (status,)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        
        return [dict(row) for row in rows]
    
    def remove_product(self, product_id: str) -> bool:
        """Remove a product from tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            return conn.total_changes > 0
    
    def update_product(self, product_id: str, **kwargs) -> bool:
        """
        Update product settings.
        
        Args:
            product_id: Product ID
            target_price: New alert threshold
            status: 'active', 'paused', 'error'
        """
        allowed = ["target_price", "status"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            for key, value in updates.items():
                conn.execute(
                    f"UPDATE products SET {key} = ? WHERE id = ?",
                    (value, product_id)
                )
            return conn.total_changes > 0