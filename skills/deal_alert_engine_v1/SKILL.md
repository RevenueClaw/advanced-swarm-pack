# Deal Alert Engine v1

Intelligent multi-channel deal alerts with rule-based notifications.

---

## Purpose

Never miss a deal. The Deal Alert Engine monitors prices across vendors and sends smart notifications only when meaningful deals occur — avoiding spam through cooldowns and suppression.

---

## Core Features

### Configurable Alert Rules

**Price Drop Alerts**
- Minimum % threshold (e.g., 5% drop)
- Minimum savings amount (e.g., $5)
- Category filtering
- Product-specific rules

**Target Price Alerts**
- Notify when price drops to or below target
- Configurable buffer (e.g., within $5)

**Stock Alerts**
- Back in stock notifications
- Low stock warnings

**Digest Mode**
- Daily summary of all deals
- Weekly best deals report

---

## Multi-Channel Support

| Channel | Priority | Setup |
|---------|----------|-------|
| Telegram | Primary | Set CHIPRADAR_TELEGRAM_BOT_TOKEN |
| Discord | Fallback | Set CHIPRADAR_DISCORD_WEBHOOK |
| Email | Fallback | Configure SMTP settings |
| Webhook | Custom | Set custom webhook URL |

---

## Quick Start

```python
from deal_alert_engine_v1 import DealAlertEngine

# Initialize
engine = DealAlertEngine()

# Check for price drop (triggers alert if rule matches)
alert = engine.check_price_drop(
    product={"id": "amazon:B08N5WRWNW", "name": "Raspberry Pi 5", "target_price": 60,
             "category": "sbc", "affiliate_link": "https://amazon.com/dp/..."},
    old_price=65.00,
    new_price=58.50
)

if alert:
    print(f"Alert sent: {alert.alert_id}")

# Check target hit
alert = engine.check_target_hit(product, current_price=58.50)

# Send daily digest
engine.send_daily_digest(
    products_checked=17,
    price_drops=[{"name": "Rock 5C", "old_price": 200, "new_price": 176}],
    target_hits=[]
)
```

---

## Default Rules

Created automatically:

1. **Price Drop 5%+** → Telegram + Discord
2. **Target Price Reached** → Telegram
3. **Back In Stock** → Telegram
4. **Daily Digest** → Telegram

---

## Rate Limiting & Spam Prevention

- **Cooldown Period**: Configurable per rule (default: 60 min)
- **Max Alerts/Day**: Configurable per rule (default: 10)
- **Auto-Suppression**: After alert sent, cooldown auto-applied
- **Manual Suppression**: `suppress_alerts(product_id, hours=24)`

---

## Alert History

```python
# Get stats
stats = engine.get_alert_stats(days=7)
print(f"Total alerts: {stats['total_alerts']}")
print(f"By channel: {stats['by_channel']}")

# View history
# Stored in SQLite: alert_history table
```

---

## Sample Alerts

**Price Drop**
```
🎉 PRICE DROP ALERT

📉 Radxa Rock 5C

💰 Was: $200.00
💵 Now: $176.00
📊 Save: 12.0% ($24.00)

🔗 [View on Amazon](...)
```

**Target Hit**
```
🎯 TARGET PRICE REACHED!

✅ Raspberry Pi 5 (4GB)

💵 Current: $58.50
🎯 Target: $60.00

🔗 [Buy Now](...)

This is at or below your target price!
```

---

## CLI Commands

```bash
# Show sample alerts
python deal_alert_engine_v1.py --demo

# View stats
python deal_alert_engine_v1.py --stats

# Test price drop
python deal_alert_engine_v1.py --test-drop "Product Name"
```

---

## Integration

Works seamlessly with:
- `multi_vendor_tracker_v1`: Cross-vendor pricing
- `price_tracker_v1`: Price history and Amazon data
- `chipradar_telegram`: Telegram notifications

---

## Configuration

Set environment variables:

```bash
export CHIPRADAR_TELEGRAM_BOT_TOKEN="..."
export CHIPRADAR_TELEGRAM_CHAT_ID="..."
export CHIPRADAR_DISCORD_WEBHOOK="..."
```
