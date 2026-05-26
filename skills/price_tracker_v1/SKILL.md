# Price Tracker v1

Multi-vendor price tracking with Amazon Creators API integration and alert notifications.

---

## Quick Start

```python
from price_tracker_v1 import PriceTracker

tracker = PriceTracker()

# Add product by ASIN
tracker.add_product("B09B8V1YZQ", target_price=29.99)

# Add by search term (auto-resolves to ASIN)
tracker.add_product("Echo Dot 5th gen", target_price=50.00)

# Check all prices
results = tracker.check_all_prices()
print(f"Found {len(results['price_drops'])} price drops")

# Generate report
report = tracker.generate_alert_report()
print(report)
```

---

## Core Methods

### `add_product(query_or_asin, target_price=None, vendor="amazon")`

Add product to tracking.

**Parameters:**
- `query_or_asin` - ASIN, URL, or search term
- `target_price` - Alert threshold
- `vendor` - "amazon", "microcenter", "pihut" (planned)

**Returns:** `{"success": True, "id": "...", ...}`

### `get_current_price(product_id)`

Fetch latest price for tracked product.

**Returns:** Current price data with source (API or scrape)

### `check_all_prices()`

Poll all tracked products.

**Returns:**
```python
{
    "checked": N,
    "price_drops": [...],
    "errors": [...],
    "status": [...]
}
```

### `get_price_history(product_id)`

Get historical price data.

**Returns:** List of `{price, currency, timestamp}`

### `generate_alert_report()`

Formatted report with affiliate links.

**Returns:** Multi-line string suitable for email/message

---

## Storage

- **Database**: `~/.openclaw/price_tracker.db` (SQLite)
- **Tables**: `products`, `price_history`
- **Privacy**: Local only, no cloud sync

---

## Security

- Credentials loaded from secure local storage
- No secrets in code
- Affiliate links use your partner tag

---

## Rate Limiting

- Built-in 1.2s delay between requests
- 1 automatic retry on 429/5xx errors
- ~50 requests/min max

---

## Integration

Requires `amazon_creators_api_v1` skill installed in sibling directory.
