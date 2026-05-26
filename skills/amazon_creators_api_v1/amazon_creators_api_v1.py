#!/usr/bin/env python3
"""
Amazon Creators API v1 - Secure Product Data Access
Fetches Amazon product data and generates affiliate links.

SECURITY: Credentials loaded from secure local storage only.
Never store real credentials in this file.
"""

import os
import json
import time
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configuration (placeholders - override via env vars)
DEFAULT_CONFIG = {
    "partner_type": "Associates",
    "oauth_scope": "creatorsapi::default",
    "token_endpoint": "https://api.amazon.com/auth/o2/token",
    "base_url": "https://creatorsapi.amazon",
    "marketplace": "www.amazon.com"
}

# Credential paths (in order of preference)
CREDENTIAL_PATHS = [
    Path.home() / ".openclaw" / "credentials" / "amazon_creators.env",
]


class AmazonCreatorsAPI:
    """
    Amazon Creators API Client
    
    Loads credentials securely from local storage.
    Supports OAuth 2.0 client credentials flow.
    """
    
    def __init__(self, partner_tag: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.credentials = self._load_credentials()
        self.partner_tag = partner_tag or self.credentials.get("partner_tag", "{{PARTNER_TAG}}")
        self.access_token: Optional[str] = None
        self.token_expires: float = 0
        
        # Validate configuration
        self._validate_config()
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load credentials from secure local storage."""
        creds = {}
        
        # Try env vars first (highest priority)
        env_vars = {
            "client_id": "AMAZON_CREATOR_CLIENT_ID",
            "client_secret": "AMAZON_CREATOR_CLIENT_SECRET",
            "partner_tag": "AMAZON_PARTNER_TAG",
            "partner_type": "AMAZON_PARTNER_TYPE",
        }
        
        for key, env_var in env_vars.items():
            value = os.getenv(env_var)
            if value:
                creds[key] = value
        
        # Try credential files
        for cred_path in CREDENTIAL_PATHS:
            if cred_path.exists():
                try:
                    with open(cred_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                key = key.strip().upper()
                                value = value.strip().strip('"\'')
                                
                                # Map to internal keys
                                if key == 'AMAZON_CREATOR_CLIENT_ID' and 'client_id' not in creds:
                                    creds['client_id'] = value
                                elif key == 'AMAZON_CREATOR_CLIENT_SECRET' and 'client_secret' not in creds:
                                    creds['client_secret'] = value
                                elif key == 'AMAZON_PARTNER_TAG' and 'partner_tag' not in creds:
                                    creds['partner_tag'] = value
                except Exception:
                    pass
        
        return creds
    
    def _validate_config(self):
        """Check required configuration is present."""
        required = ["client_id", "client_secret"]
        missing = [r for r in required if not self.credentials.get(r)]
        
        if missing:
            raise ValueError(
                f"Missing credentials: {', '.join(missing)}. "
                f"Set env vars or use {CREDENTIAL_PATHS[0]}"
            )
    
    def _get_auth_token(self) -> str:
        """Obtain OAuth access token. Auto-refreshes if expired."""
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        
        response = requests.post(
            self.config["token_endpoint"],
            json={
                "grant_type": "client_credentials",
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"],
                "scope": self.config["oauth_scope"]
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expires = time.time() + data.get("expires_in", 3600)
        
        return self.access_token
    
    def _make_request(self, endpoint: str, payload: Dict, retry: bool = True) -> Dict:
        """Make authenticated API request with retry logic."""
        token = self._get_auth_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "x-marketplace": self.config["marketplace"],
            "Content-Type": "application/json"
        }
        
        url = f"{self.config['base_url']}{endpoint}"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            # Retry on rate limit (429) or transient errors (5xx)
            if retry and (e.response.status_code == 429 or e.response.status_code >= 500):
                time.sleep(1)  # Brief delay before retry
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except Exception:
                    raise
            raise
        except requests.exceptions.ChunkedEncodingError:
            # Retry on connection issues
            if retry:
                time.sleep(1)
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except Exception:
                    raise
            raise
    
    def get_item(self, asin: str, resources: Optional[List[str]] = None) -> Dict:
        """
        Fetch product by ASIN with comprehensive pricing data.
        Prioritizes buy box winner, falls back to lowest available price.
        """
        if resources is None:
            resources = [
                "itemInfo.title",
                "itemInfo.byLineInfo",
                "images.primary.large",
                "offersV2.listings.price",
                "offersV2.listings.availability",
                "offersV2.listings.isBuyBoxWinner",
                "offersV2.listings.condition"
            ]
        
        data = self._make_request("/catalog/v1/getItems", {
            "partnerTag": self.partner_tag,
            "partnerType": self.config["partner_type"],
            "itemIds": [asin],
            "resources": resources
        })
        
        items = data.get("itemsResult", {}).get("items", [])
        
        if not items:
            return {"asin": asin, "title": None, "affiliate_link": f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"}
        
        item = items[0]
        info = item.get("itemInfo", {})
        title = info.get("title", {}).get("displayValue")
        brand = info.get("byLineInfo", {}).get("brand", {}).get("displayValue")
        
        # Build result
        result = {
            "asin": item.get("asin"),
            "title": title,
            "brand": brand,
            "detail_page_url": item.get("detailPageURL"),
            "affiliate_link": f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}",
            "images": item.get("images", {})
        }
        
        # Parse offers with intelligent prioritization
        offers = item.get("offersV2", {}).get("listings", [])
        selected_offer = None
        
        if offers:
            # Priority 1: Buy Box Winner that is available
            for offer in offers:
                if offer.get("isBuyBoxWinner") and offer.get("availability", {}).get("type") in ["Now", "InStock"]:
                    selected_offer = offer
                    break
            
            # Priority 2: Lowest price available
            if not selected_offer:
                available_offers = [
                    o for o in offers 
                    if o.get("availability", {}).get("type") in ["Now", "InStock", "Available"]
                ]
                if available_offers:
                    selected_offer = min(
                        available_offers,
                        key=lambda x: x.get("price", {}).get("amount", float('inf')) or float('inf')
                    )
            
            # Priority 3: Any offer with a price
            if not selected_offer:
                for offer in offers:
                    if offer.get("price", {}).get("amount"):
                        selected_offer = offer
                        break
            
            # Extract price data from selected offer
            if selected_offer:
                price_info = selected_offer.get("price", {})
                if price_info:
                    result["price"] = price_info.get("amount")
                    result["currency"] = price_info.get("currency")
                    result["price_display"] = price_info.get("displayAmount")
                
                result["availability"] = selected_offer.get("availability", {}).get("type")
                result["is_buy_box_winner"] = selected_offer.get("isBuyBoxWinner")
                result["condition"] = selected_offer.get("condition", {}).get("value")
        
        return result
    
    def search_items(
        self,
        keywords: str,
        search_index: Optional[str] = None,
        item_count: int = 10
    ) -> List[Dict]:
        """
        Search Amazon catalog.
        
        Args:
            keywords: Search query
            search_index: Category ("All", "Electronics", "Home", etc.)
            item_count: Max results (default 10)
        
        Returns:
            List of product dictionaries
        """
        # Default resources for comprehensive results
        resources = [
            "itemInfo.title",
            "itemInfo.byLineInfo",
            "images.primary.large",
            "offersV2.listings.price",
            "offersV2.listings.availability"
        ]
        
        # Build request with camelCase keys
        def do_search(idx: str) -> List[Dict]:
            payload = {
                "keywords": keywords,
                "searchIndex": idx,  # camelCase
                "itemCount": item_count,  # camelCase
                "resources": resources,
                "partnerTag": self.partner_tag,
                "partnerType": self.config["partner_type"],
                "marketplace": self.config["marketplace"]
            }
            
            data = self._make_request("/catalog/v1/searchItems", payload)
            return data.get("searchResult", {}).get("items", [])
        
        # Try requested index first, or "All" if none specified
        indices_to_try = [search_index] if search_index else ["All"]
        
        # Fallback categories if "All" returns nothing (only valid search indices)
        if not search_index or search_index == "All":
            indices_to_try.extend([
                "Electronics"
            ])
        
        all_results = []
        seen_asins = set()
        
        for idx in indices_to_try:
            if not idx:
                continue
            try:
                items = do_search(idx)
                for item in items:
                    asin = item.get("asin", "")
                    if asin in seen_asins:
                        continue
                    seen_asins.add(asin)
                    
                    info = item.get("itemInfo", {})
                    title = info.get("title", {}).get("displayValue") if isinstance(info.get("title"), dict) else None
                    brand = info.get("byLineInfo", {}).get("brand", {}).get("displayValue") if isinstance(info.get("byLineInfo"), dict) else None
                    
                    result = {
                        "asin": asin,
                        "title": title,
                        "brand": brand,
                        "detail_page_url": item.get("detailPageURL"),
                        "affiliate_link": f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}",
                        "images": item.get("images", {}),
                        "search_index": idx
                    }
                    
                    # Add price if available
                    offers = item.get("offersV2", {}).get("listings", [])
                    if offers:
                        price_info = offers[0].get("price", {})
                        if price_info:
                            result["price"] = price_info.get("amount")
                            result["currency"] = price_info.get("currency")
                        avail_info = offers[0].get("availability", {})
                        if avail_info:
                            result["availability"] = avail_info.get("type")
                    
                    all_results.append(result)
                    
                    if len(all_results) >= item_count:
                        return all_results[:item_count]
                        
            except Exception as e:
                print(f"Search index '{idx}' failed: {e}")
                continue
        
        return all_results

    def get_product(self, query: str) -> Union[Dict, List[Dict]]:
        """
        High-level method: Get product from query (ASIN or search term).
        
        Smart detection:
        - Looks like ASIN (Bxxxxxxxx format): Direct lookup via get_item
        - Otherwise: Search via search_items
        
        Args:
            query: Either ASIN (e.g., "B09B8V1YZQ") or search term (e.g., "Echo Dot")
        
        Returns:
            Dict for ASIN lookup, List[Dict] for search
        """
        # Check if query is an ASIN (starts with B, 10 alphanumeric chars)
        clean_query = query.strip().upper()
        is_asin = bool(re.match(r'^B[A-Z0-9]{9}$', clean_query))
        
        if is_asin:
            print(f"Detected ASIN: {clean_query} - performing direct lookup...")
            return self.get_item(clean_query)
        else:
            print(f"Detected search term: {query} - searching catalog...")
            results = self.search_items(query, search_index="All", item_count=10)
            
            # Smart fallback: if "All" returns nothing, try "Electronics", then "Home"
            if not results:
                print(f"  No results in 'All', trying 'Electronics'...")
                results = self.search_items(query, search_index="Electronics", item_count=10)
            
            if not results:
                print(f"  No results in 'Electronics', trying 'Home'...")
                results = self.search_items(query, search_index="HomeGarden", item_count=10)
            
            if not results:
                print(f"  No results found in any category.")
            else:
                print(f"  Found {len(results)} result(s)")
            
            return results


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Amazon Creators API v1 (Hardened)")
    parser.add_argument("--asin", help="Product ASIN to lookup")
    parser.add_argument("--search", help="Search keywords")
    parser.add_argument("--product", help="Smart lookup: ASIN or search term")
    parser.add_argument("--test", action="store_true", help="Run full test suite")
    
    args = parser.parse_args()
    
    api = AmazonCreatorsAPI()
    
    if args.asin:
        print(json.dumps(api.get_item(args.asin), indent=2))
    elif args.search:
        print(json.dumps(api.search_items(args.search), indent=2))
    elif args.product:
        result = api.get_product(args.product)
        print(json.dumps(result, indent=2))
    elif args.test:
        # Full test suite
        print("="*60)
        print("Amazon Creators API v1 - Full Test Suite")
        print("="*60)
        
        # Test 1: ASIN lookup
        print("\n[TEST 1] Direct ASIN lookup: B09B8V1YZQ")
        print("-"*60)
        result = api.get_product("B09B8V1YZQ")
        if isinstance(result, dict) and result.get("title"):
            print(f"✓ PASS: {result.get('title', 'N/A')[:50]}")
        else:
            print("✗ FAIL: No product data returned")
        
        # Test 2: Search
        print("\n[TEST 2] Search: Echo Dot")
        print("-"*60)
        results = api.get_product("Echo Dot")
        if isinstance(results, list) and len(results) > 0:
            print(f"✓ PASS: Found {len(results)} product(s)")
            for i, r in enumerate(results[:2], 1):
                print(f"  {i}. {r.get('title', 'N/A')[:40]}...")
        else:
            print("✗ FAIL: No results")
        
        # Test 3: Smart ASIN detection
        print("\n[TEST 3] Smart detection: lowercase 'b09b8v1yzq'")
        print("-"*60)
        result = api.get_product("b09b8v1yzq")
        if isinstance(result, dict) and result.get("title"):
            print(f"✓ PASS: Detected as ASIN, retried: {result.get('title', 'N/A')[:50]}")
        else:
            print("✗ FAIL: Detection failed")
        
        print("\n" + "="*60)
        print("Test suite complete")
        print("="*60)
