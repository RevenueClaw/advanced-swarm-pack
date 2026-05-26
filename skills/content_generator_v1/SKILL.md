# Content Generator v1

Generate affiliate content, comparison tables, and video scripts from tracked products.

---

## Purpose

Turn tracked products into money-making content automatically. Generate:
- Comparison tables (Markdown/HTML)
- "Best Under $X" buyer's guides
- YouTube scripts with affiliate links
- Blog posts with SEO optimization
- Price drop news content

---

## Core Features

### 1. Comparison Tables

```python
from content_generator_v1 import ContentGenerator

generator = ContentGenerator()

# Generate Markdown table
table = generator.generate_comparison_table(products, format="markdown")
```

**Output:**
```markdown
| Product | Price | CPU | RAM | Best For | Link |
|---|---|---|---|---|---|
| Radxa Rock 5C | $176 | RK3588S2 | 4GB | AI/ML | [Buy](...) |
| Raspberry Pi 5 | $58 | BCM2712 | 4GB | General | [Buy](...) |
```

### 2. "Best Under $X" Roundups

```python
article = generator.generate_roundup(
    title="Best Single Board Computers Under $200",
    products=products,
    max_price=200,
    format="markdown"
)
```

**Includes:**
- Title and intro
- Quick comparison table
- Detailed reviews with pros/cons
- Affiliate links
- Disclosure

### 3. YouTube Scripts

```python
video = generator.generate_youtube_script(
    product=main_product,
    alternatives=similar_products
)

print(video['script'])
print(video['description'])
print(video['tags'])
```

### 4. Price Drop Content

```python
content = generator.generate_price_drop_content(price_drops)
# Creates "Price Drop This Week" announcement
```

### 5. SEO Meta Data

```python
seo = generator.generate_seo_meta(
    title="Best SBCs Under $200",
    description="Looking for powerful single board computers that won't break the bank?",
    keywords=["SBC", "Raspberry Pi", "Rock 5", "under $200"]
)

# Returns: title_tag, meta_description, JSON-LD schema
```

---

## Content Templates

### Markdown Roundup Structure

```markdown
# [Title]

*Last updated: [Date]*

[Intro paragraph]

**Quick Comparison**

| Product | Price | ... |

## Detailed Reviews

### 1. [Product Name]
**Price:** $XXX
**Specs:** CPU | RAM
**Best for:** [Use case]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]

[Buy on Amazon →]

---

## Conclusion

[Wrap-up with disclosure]
```

### YouTube Description Template

```
[Video Title] review and comparison.

🏆 Best Overall: [Product] ($[Price])
🔗 [Affiliate Link]

CHAPTERS:
0:00 Intro
1:00 Unboxing
...

ALTERNATIVES:
• [Alt 1]: [Link]
• [Alt 2]: [Link]

#[Hashtags]
```

---

## Formats Supported

| Format | Use Case |
|--------|----------|
| `markdown` | Blog posts, GitHub, static sites |
| `html` | WordPress, custom websites |
| `plain` | Email newsletters, messages |

---

## Affiliate Integration

All links automatically include your partner tag:
```python
# From environment
AMAZON_PARTNER_TAG=vhicklegar011-20

# Generated link
https://www.amazon.com/dp/B0CYY27YZ8?tag=vhicklegar011-20
```

---

## CLI Usage

```bash
# Generate sample content
python content_generator_v1.py --demo

# Generate from products
python content_generator_v1.py --roundup "Best SBCs" --max-price 200

# Create YouTube script
python content_generator_v1.py --youtube-script --product-id B0CYY27YZ8
```

---

## Integration

Works with:
- `multi_vendor_tracker_v1`: Pull cross-vendor pricing
- `price_tracker_v1`: Get latest prices and history
- `deal_alert_engine_v1`: Generate content from price drops

---

## Best Practices

1. **Update regularly** — Regenerate content weekly with fresh prices
2. **Include disclosure** — Required for affiliate content
3. **SEO optimize** — Use generate_seo_meta() for tags
4. **Test links** — Verify affiliate links work before publishing
5. **Save templates** — Reuse successful formats

---

## Output Location

```
~/.openclaw/content_output/
├── best-sbcs-under-200.md
├── comparison-table.html
├── youtube-script-rock5c.txt
└── price-drops-week-25.md
```
