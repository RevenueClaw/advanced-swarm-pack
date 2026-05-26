#!/usr/bin/env python3
"""
Multi-Vendor Tracker v1 - Advanced Swarm Pack
Professional multi-vendor price tracking & normalization for hardware/tech products.

Integrates: amazon_creators_api_v1, skill-web-scraper, price_tracker_v1
"""

import os
import re
import json
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Configuration
DB_PATH = Path.home() / ".openclaw" / "multi_vendor_tracker.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
RATE_LIMIT_SECONDS = 2


@dataclass
class ProductPrice:
    """Normalized price data across all vendors."""
    vendor: str
    product_id: str
    name: str
    url: str
    price: Optional[float]
    currency: str
    availability: str
    list_price: Optional[float]
    sale_price: Optional[float]
    savings_amount: Optional[float]
    savings_percent: Optional[float]
    image_url: Optional[str]
    last_updated: str
    raw_data: Dict


@dataclass
class UnifiedProduct:
    """Cross-vendor product representation."""
    unified_id: str
    name: str
    category: str
    brand: Optional[str]
    model: Optional[str]
    specs: Dict[str, str]
    vendors: List[ProductPrice]
    lowest_price: Optional[float]
    highest_price: Optional[float]
    best_vendor: Optional[str]
    created_at: str
    updated_at: str


class VendorAdapters:
    """Vendor-specific parsing adapters."""
    
    @staticmethod
    def parse_micro_center(html: str, url: str) -> Optional[ProductPrice]:
        """Parse Micro Center product page."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            price_elem = soup.select_one('span#pricing') or soup.select_one('.price')
            price = None
            if price_elem:
                match = re.search(r'[\d,.]+', price_elem.text.replace(',', ''))
                if match:
                    price = float(match.group())
            
            name_elem = soup.select_one('h1 span[data-category]') or soup.select_one('h1')
            name = name_elem.text.strip() if name_elem else 'Unknown'
            
            avail_elem = soup.select_one('.inventory') or soup.select_one('.availability')
            availability = 'unknown'
            if avail_elem:
                text = avail_elem.text.lower()
                if 'in stock' in text:
                    availability = 'in_stock'
                elif 'out of stock' in text:
                    availability = 'out_of_stock'
            
            return ProductPrice(
                vendor='micro_center',
                product_id=url.split('/')[-1] if '/' in url else url,
                name=name,
                url=url,
                price=price,
                currency='USD',
                availability=availability,
                list_price=None,
                sale_price=price,
                savings_amount=None,
                savings_percent=None,
                image_url=None,
                last_updated=datetime.now().isoformat(),
                raw_data={}
            )
        except Exception as e:
            print(f"[Micro Center] Parse error: {e}")
            return None
    
    @staticmethod
    def parse_pi_hut(html: str, url: str) -> Optional[ProductPrice]:
        """Parse The Pi Hut product page."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            price_elem = soup.select_one('.price') or soup.select_one('[data-price]')
            price = None
            if price_elem:
                match = re.search(r'[\d,.]+', price_elem.text.replace(',', ''))
                if match:
                    price = float(match.group())
            
            name_elem = soup.select_one('h1.product-title')
            name = name_elem.text.strip() if name_elem else 'Unknown'
            
            return ProductPrice(
                vendor='pi_hut',
                product_id=url.split('/')[-1].split('?')[0] if '/' in url else url,
                name=name,
                url=url,
                price=price,
                currency='GBP',
                availability='unknown',
                list_price=None,
                sale_price=price,
                savings_amount=None,
                savings_percent=None,
                image_url=None,
                last_updated=datetime.now().isoformat(),
                raw_data={}
            )
        except Exception as e:
            print(f"[Pi Hut] Parse error: {e}")
            return None


class MultiVendorTracker:
    """Professional multi-vendor price tracking & normalization."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.last_request_time = {}
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    unified_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    brand TEXT,
                    model TEXT,
                    specs_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS vendor_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unified_id TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    vendor_product_id TEXT,
                    name TEXT,
                    url TEXT,
                    price REAL,
                    currency TEXT,
                    availability TEXT,
                    last_updated TEXT,
                    raw_data_json TEXT
                );
                
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unified_id TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    price REAL,
                    currency TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def _rate_limit(self, vendor: str):
        """Enforce rate limiting per vendor."""
        now = time.time()
        last = self.last_request_time.get(vendor, 0)
        elapsed = now - last
        if elapsed < RATE_LIMIT_SECONDS:
            sleep_time = RATE_LIMIT_SECONDS - elapsed
            time.sleep(sleep_time)
        self.last_request_time[vendor] = time.time()
    
    def _scrape_url(self, url: str) -> Optional[str]:
        """Scrape a URL with error handling."""
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[Scraper] Failed: {e}")
            return None
    
    def add_product(self, name: str, urls: Dict[str, str], category: str = 'hardware') -> str:
        """Add a product to track across multiple vendors."""
        unified_id = f"unified_{hash(name) % 100000:05d}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO products (unified_id, name, category, updated_at)
                VALUES (?, ?, ?, ?)
            """, (unified_id, name, category, datetime.now().isoformat()))
        
        for vendor, url in urls.items():
            print(f"[MultiVendor] Checking {vendor}: {url}")
            price_data = self._fetch_vendor(vendor, url)
            if price_data:
                self._save_price(unified_id, price_data)
        
        return unified_id
    
    def _fetch_vendor(self, vendor: str, url: str) -> Optional[ProductPrice]:
        """Fetch price from specific vendor."""
        self._rate_limit(vendor)
        html = self._scrape_url(url)
        if not html:
            return None
        
        if vendor == 'micro_center':
            return VendorAdapters.parse_micro_center(html, url)
        elif vendor == 'pi_hut':
            return VendorAdapters.parse_pi_hut(html, url)
        else:
            # Generic parser
            return ProductPrice(
                vendor=vendor,
                product_id=url,
                name='Unknown',
                url=url,
                price=None,
                currency='USD',
                availability='unknown',
                last_updated=datetime.now().isoformat(),
                raw_data={}
            )
    
    def _save_price(self, unified_id: str, price: ProductPrice):
        """Save price data to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO vendor_prices 
                (unified_id, vendor, price, currency, availability, url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (unified_id, price.vendor, price.price, price.currency, 
                  price.availability, price.url, price.last_updated))
            
            if price.price:
                conn.execute("""
                    INSERT INTO price_history (unified_id, vendor, price, currency)
                    VALUES (?, ?, ?, ?)
                """, (unified_id, price.vendor, price.price, price.currency))
    
    def get_product(self, unified_id: str) -> Optional[UnifiedProduct]:
        """Get unified product with all vendor prices."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            product_row = conn.execute(
                "SELECT * FROM products WHERE unified_id = ?", (unified_id,)
            ).fetchone()
            
            if not product_row:
                return None
            
            price_rows = conn.execute("""
                SELECT * FROM vendor_prices WHERE unified_id = ? ORDER BY last_updated DESC
            """, (unified_id,)).fetchall()
            
            vendors = []
            for row in price_rows:
                vendors.append(ProductPrice(
                    vendor=row['vendor'],
                    product_id=row['vendor_product_id'] or row['url'],
                    name=row['name'] or product_row['name'],
                    url=row['url'],
                    price=row['price'],
                    currency=row['currency'],
                    availability=row['availability'],
                    last_updated=row['last_updated'],
                    raw_data={},
                    list_price=None, sale_price=None, savings_amount=None, 
                    savings_percent=None, image_url=None
                ))
            
            prices = [v.price for v in vendors if v.price]
            
            return UnifiedProduct(
                unified_id=unified_id,
                name=product_row['name'],
                category=product_row['category'],
                brand=product_row['brand'],
                model=product_row['model'],
                specs=json.loads(product_row['specs_json'] or '{}'),
                vendors=vendors,
                lowest_price=min(prices) if prices else None,
                highest_price=max(prices) if prices else None,
                best_vendor=None,
                created_at=product_row['created_at'],
                updated_at=product_row['updated_at']
            )


def main():
    """CLI for multi-vendor tracker."""
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Vendor Tracker v1")
    parser.add_argument("--add", help="Add product name")
    parser.add_argument("--urls", help="JSON dict of vendor URLs")
    parser.add_argument("--get", help="Get product by unified ID")
    
    args = parser.parse_args()
    
    tracker = MultiVendorTracker()
    
    if args.add and args.urls:
        urls = json.loads(args.urls)
        uid = tracker.add_product(args.add, urls)
        print(f"Added: {uid}")
    elif args.get:
        product = tracker.get_product(args.get)
        if product:
            print(f"Product: {product.name}")
            for v in product.vendors:
                print(f"  - {v.vendor}: ${v.price}")


if __name__ == "__main__":
    main()
