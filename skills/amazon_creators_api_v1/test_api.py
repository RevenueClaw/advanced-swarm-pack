#!/usr/bin/env python3
"""Test script for Amazon Creators API skill."""

import sys
sys.path.insert(0, '.')

from amazon_creators_api_v1 import AmazonCreatorsAPI

def test_get_item():
    """Test fetching product by ASIN."""
    print("="*60)
    print("Test: Get Item (ASIN: B08N5WRWNW)")
    print("="*60)
    
    try:
        api = AmazonCreatorsAPI()
        product = api.get_item("B08N5WRWNW")
        
        print(f"\n✓ SUCCESS!")
        print(f"ASIN: {product.asin}")
        print(f"Title: {product.title}")
        print(f"Price: {product.price} {product.currency}")
        print(f"Brand: {product.brand}")
        print(f"Image: {product.image_url}")
        print(f"Affiliate Link: {product.affiliate_link}")
        
        return True
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

def test_search():
    """Test search items."""
    print("\n" + "="*60)
    print("Test: Search Items (keywords: 'laptop')")
    print("="*60)
    
    try:
        api = AmazonCreatorsAPI()
        products = api.search_items("laptop", search_index="Electronics", item_page=1)
        
        print(f"\n✓ SUCCESS! Found {len(products)} items")
        for i, p in enumerate(products[:3], 1):
            print(f"\n{i}. {p.title}")
            print(f"   Price: {p.price} {p.currency}")
            print(f"   Link: {p.affiliate_link}")
        
        return True
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Amazon Creators API v1 - Test Suite")
    print("="*60)
    
    results = []
    results.append(("Get Item", test_get_item()))
    results.append(("Search Items", test_search()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
