#!/usr/bin/env python3
"""
Deal Alert Engine v1 - Advanced Swarm Pack
Intelligent multi-channel deal alerts with rule-based notifications.

Integrates: multi_vendor_tracker_v1, price_tracker_v1, chipradar_telegram
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration
DB_PATH = Path.home() / ".openclaw" / "deal_alert_engine.db"
ALERT_COOLDOWN_MINUTES = 60  # Don't alert same product within this time


class AlertType(Enum):
    PRICE_DROP = "price_drop"
    TARGET_HIT = "target_hit"
    BACK_IN_STOCK = "back_in_stock"
    LOW_STOCK = "low_stock"
    BEST_PRICE = "best_price"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_BEST = "weekly_best"


class AlertChannel(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    DISCORD = "discord"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """Configurable alert rule."""
    rule_id: str
    name: str
    alert_type: AlertType
    enabled: bool = True
    channels: List[AlertChannel] = None
    
    # Condition thresholds
    min_price_drop_percent: float = 5.0  # e.g., 5% drop
    min_savings_amount: float = 5.0     # e.g., $5 savings
    target_price_buffer: float = 0.0    # e.g., within $X of target
    
    # Rate limiting
    cooldown_minutes: int = 60
    max_alerts_per_day: int = 10
    
    # Filtering
    product_categories: List[str] = None
    specific_products: List[str] = None  # Unified IDs
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [AlertChannel.TELEGRAM]
        if self.product_categories is None:
            self.product_categories = []
        if self.specific_products is None:
            self.specific_products = []


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    product_id: str
    product_name: str
    message: str
    data: Dict  # Original price data
    channels_sent: List[AlertChannel]
    sent_at: str
    suppressed: bool = False


class DealAlertEngine:
    """
    Intelligent deal alert engine with multi-channel support.
    
    Features:
    - Configurable alert rules (price drop %, target hit, stock changes)
    - Multi-channel: Telegram, Email, Discord, Webhooks
    - Rate limiting and spam suppression
    - Alert history and statistics
    - Daily digest and weekly best deals
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Channel configurations
        self.telegram_token = os.getenv("CHIPRADAR_TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("CHIPRADAR_TELEGRAM_CHAT_ID", "")
        self.discord_webhook = os.getenv("CHIPRADAR_DISCORD_WEBHOOK", "")
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", ""),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASS", ""),
            "from_email": os.getenv("ALERT_FROM_EMAIL", ""),
        }
        
        self._init_db()
        self._load_default_rules()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    channels_json TEXT,
                    thresholds_json TEXT,
                    filters_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS alert_history (
                    alert_id TEXT PRIMARY KEY,
                    rule_id TEXT,
                    alert_type TEXT,
                    product_id TEXT,
                    product_name TEXT,
                    message TEXT,
                    data_json TEXT,
                    channels_json TEXT,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    suppressed INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS alert_suppression (
                    product_id TEXT,
                    alert_type TEXT,
                    suppressed_until TEXT,
                    reason TEXT,
                    PRIMARY KEY (product_id, alert_type)
                );
                
                CREATE INDEX IF NOT EXISTS idx_alerts_product ON alert_history(product_id);
                CREATE INDEX IF NOT EXISTS idx_alerts_time ON alert_history(sent_at);
                CREATE INDEX IF NOT EXISTS idx_alerts_type ON alert_history(alert_type);
            """)
    
    def _load_default_rules(self):
        """Load default alert rules if none exist."""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM alert_rules").fetchone()[0]
            
            if count == 0:
                # Price drop rule (5%+)
                self.add_rule(AlertRule(
                    rule_id="price_drop_5pct",
                    name="Price Drop 5%+",
                    alert_type=AlertType.PRICE_DROP,
                    min_price_drop_percent=5.0,
                    channels=[AlertChannel.TELEGRAM, AlertChannel.DISCORD],
                    cooldown_minutes=60
                ))
                
                # Target price hit
                self.add_rule(AlertRule(
                    rule_id="target_hit",
                    name="Target Price Reached",
                    alert_type=AlertType.TARGET_HIT,
                    channels=[AlertChannel.TELEGRAM],
                    cooldown_minutes=1440  # Once per day max
                ))
                
                # Back in stock
                self.add_rule(AlertRule(
                    rule_id="back_in_stock",
                    name="Back In Stock",
                    alert_type=AlertType.BACK_IN_STOCK,
                    channels=[AlertChannel.TELEGRAM],
                    cooldown_minutes=720  # Twice per day max
                ))
                
                # Daily digest
                self.add_rule(AlertRule(
                    rule_id="daily_digest",
                    name="Daily Digest",
                    alert_type=AlertType.DAILY_DIGEST,
                    channels=[AlertChannel.TELEGRAM],
                    cooldown_minutes=1440
                ))
                
                print(f"[DealAlertEngine] Created {5} default rules")
    
    def add_rule(self, rule: AlertRule) -> bool:
        """Add or update an alert rule."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_rules
                    (rule_id, name, alert_type, enabled, channels_json, thresholds_json, filters_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id,
                    rule.name,
                    rule.alert_type.value,
                    1 if rule.enabled else 0,
                    json.dumps([c.value for c in rule.channels]),
                    json.dumps({
                        "min_price_drop_percent": rule.min_price_drop_percent,
                        "min_savings_amount": rule.min_savings_amount,
                        "target_price_buffer": rule.target_price_buffer,
                        "cooldown_minutes": rule.cooldown_minutes,
                        "max_alerts_per_day": rule.max_alerts_per_day,
                    }),
                    json.dumps({
                        "product_categories": rule.product_categories,
                        "specific_products": rule.specific_products,
                        "min_price": rule.min_price,
                        "max_price": rule.max_price,
                    })
                ))
            return True
        except Exception as e:
            print(f"[DealAlertEngine] Failed to add rule: {e}")
            return False
    
    def get_rules(self, enabled_only: bool = True) -> List[AlertRule]:
        """Get all alert rules."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if enabled_only:
                rows = conn.execute("SELECT * FROM alert_rules WHERE enabled = 1").fetchall()
            else:
                rows = conn.execute("SELECT * FROM alert_rules").fetchall()
            
            rules = []
            for row in rows:
                thresholds = json.loads(row['thresholds_json'] or '{}')
                filters = json.loads(row['filters_json'] or '{}')
                
                rules.append(AlertRule(
                    rule_id=row['rule_id'],
                    name=row['name'],
                    alert_type=AlertType(row['alert_type']),
                    enabled=bool(row['enabled']),
                    channels=[AlertChannel(c) for c in json.loads(row['channels_json'] or '[]')],
                    min_price_drop_percent=thresholds.get('min_price_drop_percent', 5.0),
                    min_savings_amount=thresholds.get('min_savings_amount', 5.0),
                    target_price_buffer=thresholds.get('target_price_buffer', 0.0),
                    cooldown_minutes=thresholds.get('cooldown_minutes', 60),
                    max_alerts_per_day=thresholds.get('max_alerts_per_day', 10),
                    product_categories=filters.get('product_categories', []),
                    specific_products=filters.get('specific_products', []),
                    min_price=filters.get('min_price'),
                    max_price=filters.get('max_price'),
                ))
            
            return rules
    
    def check_price_drop(self, product: Dict, old_price: float, new_price: float) -> Optional[Alert]:
        """
        Check if price drop triggers any rules.
        
        Args:
            product: Product dict with id, name, category, target_price, etc.
            old_price: Previous price
            new_price: Current price
        
        Returns:
            Alert object if triggered, None otherwise
        """
        if not old_price or not new_price or new_price >= old_price:
            return None
        
        drop_pct = ((old_price - new_price) / old_price) * 100
        savings = old_price - new_price
        
        # Get applicable rules
        rules = self.get_rules(enabled_only=True)
        price_drop_rules = [r for r in rules if r.alert_type == AlertType.PRICE_DROP]
        
        for rule in price_drop_rules:
            # Check cooldown
            if self._is_on_cooldown(product['id'], AlertType.PRICE_DROP, rule.cooldown_minutes):
                continue
            
            # Check thresholds
            if drop_pct < rule.min_price_drop_percent:
                continue
            if savings < rule.min_savings_amount:
                continue
            
            # Check category filter
            if rule.product_categories and product.get('category') not in rule.product_categories:
                continue
            
            # Check specific products filter
            if rule.specific_products and product['id'] not in rule.specific_products:
                continue
            
            # Check price range
            if rule.min_price and new_price < rule.min_price:
                continue
            if rule.max_price and new_price > rule.max_price:
                continue
            
            # Create alert
            message = self._format_price_drop_alert(product, old_price, new_price, drop_pct)
            alert = self._create_alert(rule, AlertType.PRICE_DROP, product, message, {
                "old_price": old_price,
                "new_price": new_price,
                "drop_percent": drop_pct,
                "savings": savings
            })
            
            # Send to channels
            self._send_alert(alert)
            return alert
        
        return None
    
    def check_target_hit(self, product: Dict, current_price: float) -> Optional[Alert]:
        """Check if target price is hit."""
        target = product.get('target_price')
        if not target or current_price > target:
            return None
        
        rules = self.get_rules(enabled_only=True)
        target_rules = [r for r in rules if r.alert_type == AlertType.TARGET_HIT]
        
        for rule in target_rules:
            if self._is_on_cooldown(product['id'], AlertType.TARGET_HIT, rule.cooldown_minutes):
                continue
            
            message = self._format_target_hit_alert(product, current_price)
            alert = self._create_alert(rule, AlertType.TARGET_HIT, product, message, {
                "current_price": current_price,
                "target_price": target
            })
            
            self._send_alert(alert)
            return alert
        
        return None
    
    def check_stock_change(self, product: Dict, old_status: str, new_status: str) -> Optional[Alert]:
        """Check for stock availability changes."""
        # Back in stock
        if old_status in ['out_of_stock', 'unavailable'] and new_status == 'in_stock':
            rules = [r for r in self.get_rules() if r.alert_type == AlertType.BACK_IN_STOCK]
            for rule in rules:
                if self._is_on_cooldown(product['id'], AlertType.BACK_IN_STOCK, rule.cooldown_minutes):
                    continue
                
                message = f"🎉 {product['name']} is back in stock!"
                alert = self._create_alert(rule, AlertType.BACK_IN_STOCK, product, message, {
                    "old_status": old_status,
                    "new_status": new_status
                })
                self._send_alert(alert)
                return alert
        
        return None
    
    def send_daily_digest(self, products_checked: int, price_drops: List[Dict], 
                          target_hits: List[Dict]) -> Optional[Alert]:
        """Send daily digest of all deals."""
        rules = [r for r in self.get_rules() if r.alert_type == AlertType.DAILY_DIGEST]
        if not rules:
            return None
        
        rule = rules[0]  # Use first daily digest rule
        
        if self._is_on_cooldown("_digest_", AlertType.DAILY_DIGEST, rule.cooldown_minutes):
            return None
        
        message = self._format_daily_digest(products_checked, price_drops, target_hits)
        alert = self._create_alert(rule, AlertType.DAILY_DIGEST, 
                                   {"id": "_digest_", "name": "Daily Digest"},
                                   message, {
            "products_checked": products_checked,
            "price_drops": price_drops,
            "target_hits": target_hits
        })
        
        self._send_alert(alert)
        return alert
    
    def send_weekly_best_deals(self, best_deals: List[Dict]) -> Optional[Alert]:
        """Send weekly best deals summary."""
        rules = [r for r in self.get_rules() if r.alert_type == AlertType.WEEKLY_BEST]
        if not rules:
            return None
        
        rule = rules[0]
        
        if self._is_on_cooldown("_weekly_", AlertType.WEEKLY_BEST, rule.cooldown_minutes):
            return None
        
        message = self._format_weekly_best(best_deals)
        alert = self._create_alert(rule, AlertType.WEEKLY_BEST,
                                   {"id": "_weekly_", "name": "Weekly Best Deals"},
                                   message, {"best_deals": best_deals})
        
        self._send_alert(alert)
        return alert
    
    def _is_on_cooldown(self, product_id: str, alert_type: AlertType, 
                        cooldown_minutes: int) -> bool:
        """Check if product is on cooldown for this alert type."""
        # Check suppression table
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT suppressed_until FROM alert_suppression
                WHERE product_id = ? AND alert_type = ?
            """, (product_id, alert_type.value)).fetchone()
            
            if row and row[0]:
                until = datetime.fromisoformat(row[0])
                if until > datetime.now():
                    return True
        
        # Check recent alerts
        since = (datetime.now() - timedelta(minutes=cooldown_minutes)).isoformat()
        count = conn.execute("""
            SELECT COUNT(*) FROM alert_history
            WHERE product_id = ? AND alert_type = ? AND sent_at > ?
        """, (product_id, alert_type.value, since)).fetchone()[0]
        
        return count > 0
    
    def _create_alert(self, rule: AlertRule, alert_type: AlertType, 
                      product: Dict, message: str, data: Dict) -> Alert:
        """Create alert record."""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product['id'][:8]}"
        
        return Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            alert_type=alert_type,
            product_id=product['id'],
            product_name=product['name'],
            message=message,
            data=data,
            channels_sent=[],
            sent_at=datetime.now().isoformat()
        )
    
    def _send_alert(self, alert: Alert) -> bool:
        """Send alert to all configured channels."""
        # Get rule channels
        rules = self.get_rules()
        rule = next((r for r in rules if r.rule_id == alert.rule_id), None)
        
        if not rule:
            return False
        
        success = False
        for channel in rule.channels:
            try:
                if channel == AlertChannel.TELEGRAM:
                    if self._send_telegram(alert.message):
                        alert.channels_sent.append(channel)
                        success = True
                
                elif channel == AlertChannel.DISCORD:
                    if self._send_discord(alert.message):
                        alert.channels_sent.append(channel)
                        success = True
                
                elif channel == AlertChannel.EMAIL:
                    if self._send_email(alert.product_name, alert.message):
                        alert.channels_sent.append(channel)
                        success = True
            
            except Exception as e:
                print(f"[DealAlertEngine] Failed to send to {channel.value}: {e}")
        
        # Save alert to history
        self._save_alert(alert)
        
        # Update suppression
        if success:
            self._update_suppression(alert.product_id, alert.alert_type, rule.cooldown_minutes)
        
        return success
    
    def _save_alert(self, alert: Alert):
        """Save alert to history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alert_history
                (alert_id, rule_id, alert_type, product_id, product_name, message,
                 data_json, channels_json, sent_at, suppressed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.rule_id,
                alert.alert_type.value,
                alert.product_id,
                alert.product_name,
                alert.message,
                json.dumps(alert.data),
                json.dumps([c.value for c in alert.channels_sent]),
                alert.sent_at,
                1 if alert.suppressed else 0
            ))
    
    def _update_suppression(self, product_id: str, alert_type: AlertType, 
                            cooldown_minutes: int):
        """Update suppression record."""
        until = (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alert_suppression
                (product_id, alert_type, suppressed_until, reason)
                VALUES (?, ?, ?, ?)
            """, (product_id, alert_type.value, until, f"Cooldown: {cooldown_minutes}min"))
    
    def _send_telegram(self, message: str) -> bool:
        """Send Telegram message."""
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"[Telegram] Send failed: {e}")
            return False
    
    def _send_discord(self, message: str) -> bool:
        """Send Discord webhook message."""
        if not self.discord_webhook:
            return False
        
        try:
            payload = {
                "content": message,
                "username": "ChipRadar Deals"
            }
            response = requests.post(self.discord_webhook, json=payload, timeout=30)
            return response.status_code == 204
        except Exception as e:
            print(f"[Discord] Send failed: {e}")
            return False
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send email alert."""
        if not self.email_config['smtp_server']:
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(body)
            msg['Subject'] = f"[ChipRadar] {subject}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['username']
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                             self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], 
                           self.email_config['password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"[Email] Send failed: {e}")
            return False
    
    # Format methods
    def _format_price_drop_alert(self, product: Dict, old_price: float, 
                                  new_price: float, drop_pct: float) -> str:
        """Format price drop alert message."""
        savings = old_price - new_price
        return f"""🎉 *PRICE DROP ALERT*

📉 *{product['name']}*

💰 Was: ${old_price:.2f}
💵 Now: ${new_price:.2f}
📊 Save: {drop_pct:.1f}% (${savings:.2f})

🔗 [View on Amazon]({product.get('affiliate_link', '#')})

_Target: ${product.get('target_price', 'N/A')}_

⏰ Alert ID: {datetime.now().strftime('%H:%M')}"""
    
    def _format_target_hit_alert(self, product: Dict, current_price: float) -> str:
        """Format target hit alert message."""
        return f"""🎯 *TARGET PRICE REACHED!*

✅ *{product['name']}*

💵 Current: ${current_price:.2f}
🎯 Target: ${product['target_price']:.2f}

🔗 [Buy Now]({product.get('affiliate_link', '#')})

*This is at or below your target price!*

⏰ Alert ID: {datetime.now().strftime('%H:%M')}"""
    
    def _format_daily_digest(self, products_checked: int, price_drops: List[Dict],
                             target_hits: List[Dict]) -> str:
        """Format daily digest message."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = f"""📊 *ChipRadar Daily Digest*
_{now}_

📦 Products Checked: {products_checked}
📉 Price Drops: {len(price_drops)}
🎯 Target Reached: {len(target_hits)}
"""
        
        if price_drops:
            message += "\n📉 *Recent Price Drops:*\n"
            for drop in price_drops[:5]:
                message += f"• {drop['name'][:35]}: ${drop['old_price']:.2f} → ${drop['new_price']:.2f}\n"
        
        if target_hits:
            message += "\n🎯 *Target Prices Hit:*\n"
            for hit in target_hits[:3]:
                message += f"• {hit['name'][:35]}: ${hit['price']:.2f}\n"
        
        return message
    
    def _format_weekly_best(self, best_deals: List[Dict]) -> str:
        """Format weekly best deals message."""
        now = datetime.now().strftime("%Y-%m-%d")
        
        message = f"""🏆 *ChipRadar Weekly Best Deals*
_{now}_

Top {len(best_deals)} deals this week:
"""
        
        for i, deal in enumerate(best_deals[:5], 1):
            savings = deal.get('savings_pct', 0)
            message += f"""
{i}. *{deal.get('name', 'Unknown')[:40]}*
   💵 ${deal.get('price', 0):.2f}
   📊 Save {savings:.0f}%
   🔗 [Buy]({deal.get('affiliate_link', '#')})
"""
        
        return message
    
    # Public API
    def suppress_alerts(self, product_id: str, duration_hours: int = 24, 
                       reason: str = "") -> bool:
        """Manually suppress alerts for a product."""
        until = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            for alert_type in AlertType:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_suppression
                    (product_id, alert_type, suppressed_until, reason)
                    VALUES (?, ?, ?, ?)
                """, (product_id, alert_type.value, until, reason))
        
        return True
    
    def get_alert_stats(self, days: int = 7) -> Dict:
        """Get alert statistics."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("""
                SELECT COUNT(*) FROM alert_history WHERE sent_at > ?
            """, (since,)).fetchone()[0]
            
            by_type = conn.execute("""
                SELECT alert_type, COUNT(*) 
                FROM alert_history 
                WHERE sent_at > ?
                GROUP BY alert_type
            """, (since,)).fetchall()
            
            by_channel = conn.execute("""
                SELECT json_each.value, COUNT(*)
                FROM alert_history, json_each(channels_json)
                WHERE sent_at > ?
                GROUP BY json_each.value
            """, (since,)).fetchall()
        
        return {
            "total_alerts": total,
            "by_type": {t: c for t, c in by_type},
            "by_channel": {c: n for c, n in by_channel},
            "period_days": days
        }


def main():
    """CLI for deal alert engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deal Alert Engine v1")
    parser.add_argument("--test-drop", help="Test price drop alert")
    parser.add_argument("--test-target", help="Test target hit alert")
    parser.add_argument("--stats", action="store_true", help="Show alert stats")
    parser.add_argument("--suppress", help="Suppress product alerts (ID)")
    parser.add_argument("--demo", action="store_true", help="Show sample alerts")
    
    args = parser.parse_args()
    
    engine = DealAlertEngine()
    
    if args.demo:
        print("Deal Alert Engine v1 Demo")
        print("=" * 60)
        print("\nSample Price Drop Alert:")
        print(engine._format_price_drop_alert(
            {"name": "Radxa Rock 5C", "id": "test", "target_price": 150, "affiliate_link": "#"},
            200.00, 176.00, 12.0
        ))
        print("\n" + "=" * 60)
        print("\nSample Target Hit Alert:")
        print(engine._format_target_hit_alert(
            {"name": "Raspberry Pi 5", "id": "test", "target_price": 60, "affiliate_link": "#"},
            58.50
        ))
    
    elif args.stats:
        stats = engine.get_alert_stats()
        print(f"Alert Stats (last {stats['period_days']} days):")
        print(f"  Total: {stats['total_alerts']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  By channel: {stats['by_channel']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()