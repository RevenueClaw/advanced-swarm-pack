# Content Pipeline (v1)

Automated content generation and traffic optimization for revenue sites.

## Philosophy

**Content is a revenue asset.** Generate, update, and optimize content with the same safety rigor as code deployments.

## Quick Start

```python
from lib.content_generator import ContentGenerator
from lib.traffic_optimizer import TrafficOptimizer

gen = ContentGenerator()
optimizer = TrafficOptimizer()

# Generate SEO-optimized content
content = gen.generate_review(
    product="Radxa Rock 5C",
    template="detailed-review",
    seo_target="rock 5c review 2026"
)

# Optimize for traffic
optimized = optimizer.optimize_for_search(
    content=content,
    target_keywords=["radxa rock 5c", "sbc comparison", "ARM performance"],
    readability_target=60  # Flesch Reading Ease
)

# Schedule safe deployment
from skill_revenue_site_generator.lib import SafeDeployer
deployer = SafeDeployer("/var/www/revenue-sites")
deployer.deploy_content(optimized, path="/blog/rock-5c-review.html")
```

## Content Generation

**Template Types:**
- `detailed-review` - In-depth product reviews with benchmarks
- `comparison-article` - Side-by-side comparisons
- `buying-guide` - Educational content → conversions
- `deal-alert` - Time-sensitive price drops
- `update-log` - Changelog-style update notices

**SEO Features:**
- Auto keyword density calculation
- Internal linking recommendations
- Meta description generation
- Schema markup for articles
- Readability scoring

## Traffic Optimization

```python
# A/B test headlines
optimizer.test_headlines(
    variants=[
        "Rock 5C Review: Best SBC Under $80",
        "Radxa Rock 5C: Pi 5 Killer?",
        "Rock 5C vs Pi 5: Which Should You Buy?"
    ],
    traffic_percentage=30  # Test on 30% of traffic
)

# Internal linking optimization
optimizer.suggest_internal_links(
    new_article="rock-5c-review",
    existing_articles=site.get_all_articles(),
    strategy="revenue-maximizing"  # Prioritize high-converting pages
)

# Content freshness scheduling
optimizer.schedule_content_refresh(
    freshness_threshold=30,  # Days
    on_stale="auto-update"  # Or "notify-admin"
)
```

## Revenue Safety

```python
# Before updating high-traffic content, run premortem
from skill_premortem_v1.lib import PremortemAnalyzer

analyzer = PremortemAnalyzer()
analysis = analyzer.analyze_risk(
    goal=f"Update top-performing article: {article.title}",
    steps=[
        "Backup current version",
        "Generate updated content",
        "Stage and test",
        "Deploy with traffic split"
    ],
    context=f"Article gets {article.monthly_traffic} visits/month, ${article.revenue_30d} revenue"
)

if analysis["most_likely_failure"]["impact"] == "revenue-loss":
    # Extra precautions for high-value content
    deployer.deploy_with_traffic_split(update, percentage=10)  # 10% test
```

## Files

- `lib/content_generator.py` - Article generation engine
- `lib/traffic_optimizer.py` - SEO and conversion optimization
- `lib/content_scheduler.py` - Automated publishing pipeline
- `templates/` - Content templates

## Integration Examples

**Feature a new SBC:**
```python
# 1. Generate content
guide = gen.generate_buying_guide(
    topic="Best SBCs for Home Server 2026",
    featured_products=[rock5c, pi5, orangepi5]
)

# 2. Optimize for traffic
optimized = optimizer.optimize_for_search(guide)

# 3. Safe deploy with premortem
result = safe_deployer.deploy_with_rollback(
    content=optimized,
    path="/guides/best-sbc-home-server-2026.html",
    health_check=lambda: check_ctr_above(0.05)  # 5% CTR minimum
)
```
