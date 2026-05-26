# Multi-Vendor Tracker v1

Professional multi-vendor price tracking & normalization for hardware/tech products.

---

## Purpose

Track prices across multiple vendors (Amazon, Micro Center, The Pi Hut, Pimoroni, AliExpress) with:
- Vendor-specific parsers for accurate data extraction
- Price normalization (currency conversion, handling out-of-stock)
- Smart routing: API preferred, web scraper fallback
- Unified product schema across all vendors

---

## Supported Vendors

| Vendor | Method | Notes |
|--------|--------|-------|
| Amazon | API + Scraper | Primary; Creators API, fallback to HTML parse |
| Micro Center | Scraper | Good for US retail prices |
| The Pi Hut | Scraper | UK vendor, specializes in Raspberry Pi |
| Pimoroni | Scraper | UK vendor, Great for accessories |
| AliExpress | Scraper | Often lowest prices, longer shipping |

---

## Quick Start

```python
from multi_vendor_tracker_v1 import MultiVendorTracker

tracker = MultiVendorTracker()

# Add product with multiple vendor URLs
unified_id = tracker.add_product(
    name="Raspberry Pi 5",
    urls={
        "amazon": "B08N5WRWNW",
        "micro_center": "https://www.microcenter.com/product/...",
        "pi_hut": "https://thepihut.com/products/..."
    },
    category="sbc",
    specs={"ram": "4GB", "cpu": "BCM2712"}
)

# Get current prices from all vendors
product = tracker.get_product(unified_id)
print(f"Best price: ${product.lowest_price} from {product.best_vendor}")

for vendor in product.vendors:
    print(f"  - {vendor.vendor}: ${vendor.price} ({vendor.availability})")
```

---

## Smart Routing

```python
# Automatically routes to best method:
- Amazon ASIN → Creators API → Scraper fallback
- Micro Center/Pi Hut/Pimoroni → Direct scraping
- Unknown URL → Vendor detection → Appropriate scraper
```

---

## Price Normalization

```python
# Normalize to USD
price_gbp = tracker.fetch_product(pi_hut_url)  # Returns GBP
price_usd = tracker.normalize_price(price_gbp, 'USD')  # Converts
```

---

## CLI Usage

```bash
# Add product
python multi_vendor_tracker_v1.py \
  --add "Radxa Rock 5C" \
  --urls '{"amazon": "B0CYY27YZ8", "micro_center": "https://..."}'

# Check single URL
python multi_vendor_tracker_v1.py --check "https://thepihut.com/products/..."

# Check all tracked products
python multi_vendor_tracker_v1.py --check-all

# Get product info
python multi_vendor_tracker_v1.py --get "unified_12345"
```

---

## Database Schema

**products**: Unified product catalog
- unified_id, name, category, brand, model, specs_json

**vendor_prices**: Latest prices per vendor
- unified_id, vendor, price, currency, availability, url, last_updated

**price_history**: Time-series price data
- unified_id, vendor, price, currency, timestamp

---

## Integration

Works seamlessly with:
- `price_tracker_v1`: For price history and alerts
- `amazon_creators_api_v1`: For Amazon data
- `skill-web-scraper`: For vendor site scraping

---

## Rate Limiting

- 2 second delay between requests to same vendor
- Respects robots.txt (user-agent rotation)
- Retry on 429/5xx errors

---

## Security

- No credentials stored in code
- All DB files 600 permissions
- Affiliate links support (pass partner_tag)
