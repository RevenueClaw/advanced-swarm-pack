# Revenue Site Generator (v1)

Generate and manage revenue-generating affiliate sites with production-safe deployment practices.

## Philosophy

**Revenue sites are production systems.** Every change can affect income. Apply premortem analysis and safe editing protocols to all revenue-critical deployments.

## Quick Start

```python
from lib.site_generator import RevenueSiteGenerator
from lib.safe_deployer import SafeDeployer

gen = RevenueSiteGenerator()
deployer = SafeDeployer("/var/www/revenue-sites")

# Generate affiliate comparison page
site = gen.generate_comparison_site(
    niche="sbc-deals",
    products=["Rock 5C", "Pi 5", "Orange Pi 5"],
    template="comparison-table",
    affiliate_tag="vhicklegar011-20"
)

# Deploy with full safety
result = deployer.deploy(site, domain="deals.chipradar.com")
# Backup created, rollback ready, revenue preserved
```

## Core Capabilities

### Site Generation

**Template Types:**
- `comparison-table` - Side-by-side product comparisons (best for conversions)
- `best-under-X` - Curated lists (best SBCs under $100)
- `deal-alert-hub` - Real-time price drop listings
- `review-aggregation` - SEO-focused review compilations
- `buying-guide` - Educational → affiliate conversion funnels

**SEO Optimization:**
- Auto-generated meta descriptions with price points
- Schema.org Product markup for rich snippets
- Affiliate link cloaking (no raw Amazon URLs visible)
- Lazy-loaded images for Core Web Vitals

### Revenue-Focused Features

```python
# Conversion tracking
gen.add_conversion_tracking(
    site_id="sbc-deals-v1",
    events=["click", "add_to_cart", "purchase_intent"]
)

# A/B testing framework
gen.enable_ab_testing(
    test_name="cta-button-color",
    variants=["orange", "green", "blue"],
    traffic_split=[0.34, 0.33, 0.33]
)

# Price freshness validation
gen.add_price_refresh(
    frequency="6_hours",
    source="chipradar_api",
    stale_price_action="hide"  # Don't show prices >24h old
)

### Safe Deployment Protocol

Every deployment follows the Safe Edit Protocol:

1. **Timestamped backup** of current site
2. **Atomic deployment** (symlink swap: staging → production)
3. **Health check** post-deploy (HTTP 200, affiliate links work)
4. **Rollback plan** (instant revert via symlink)

```python
# Safe deployment with automatic rollback
deployer.deploy_with_rollback(
    site=site,
    domain="deals.chipradar.com",
    health_check=lambda: check_affiliate_links_work(),
    on_failure="rollback"  # Auto-rollback if revenue drops
)
```

### Premortem for Revenue Sites

Before any deployment, run premortem analysis:

```python
from skill_premortem_v1.lib import PremortemAnalyzer

pa = PremortemAnalyzer()
analysis = pa.premortem(
    goal="Deploy new ChipRadar deals site",
    proposed_plan=[
        "Generate site with latest prices",
        "Deploy to production",
        "Update CloudFlare cache",
        "Verify affiliate links"
    ],
    context="Revenue-critical: site generates $X/month in affiliate revenue",
    risk_tolerance="low"  # Revenue sites are never "high risk tolerance"
)

# Most likely failure: "Stale prices after deployment due to API cache"
# Mitigation: Verified in deploy_with_rollback health check
```

## Integration with ChipRadar

```python
# Real-time price integration
from lib.chipradar_integration import ChipRadarFeed

feed = ChipRadarFeed()
site = gen.generate_deal_site(
    products=feed.get_trending_deals(min_profit_margin=20),
    auto_update=True  # Refresh prices via webhook
)

# Database connection (runtime, not import-time)
# Uses connection pooling with failover
```

## Safe Editing for Live Sites

```python
from skill_codebase_understander_v1.lib import SafeEditProtocol

editor = SafeEditProtocol(
    project_path="/var/www/revenue-sites/deals",
    backup_dir="/backups/revenue-sites"
)

# Safe content update
result = editor.safe_edit(
    file_path="index.html",
    content=new_deals_content,
    verify_syntax=lambda c: validate_html(c) and check_affiliate_links(c),
    verify_integrity=True
)

if not result['success']:
    editor.rollback("index.html", result['backup_id'])
    alert_revenue_team("Deploy failed, rolled back")
```

## Files

- `lib/site_generator.py` - Core generation engine
- `lib/template_engine.py` - Jinja2 templates for revenue sites
- `lib/safe_deployer.py` - Atomic deployment with rollback
- `lib/chipradar_integration.py` - Real-time price feeds
- `lib/ab_testing.py` - Conversion optimization
- `templates/` - Revenue-optimized HTML templates

## Anti-Patterns (Never Do)

❌ Deploy Friday at 5 PM  
❌ Edit live site without backup  
❌ Import-time DB connections (affects cold start)  
❌ Deploy without health checks  
❌ Let stale prices show for >24 hours  

✅ Deploy Tuesday 10 AM  
✅ Timestamped backups with every edit  
✅ Runtime path resolution  
✅ Automated health checks + rollback  
✅ Price freshness validation before render  
