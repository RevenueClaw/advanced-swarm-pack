#!/usr/bin/env python3
"""
Content Generator v1 - Advanced Swarm Pack
Generate affiliate content, comparison tables, and video scripts from tracked products.

Integrates: multi_vendor_tracker_v1, price_tracker_v1, deal_alert_engine_v1
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass

# Add dependencies to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'multi_vendor_tracker_v1'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'price_tracker_v1'))

try:
    from multi_vendor_tracker_v1 import MultiVendorTracker, UnifiedProduct
    from price_tracker_v1 import PriceTracker
except ImportError:
    MultiVendorTracker = None
    PriceTracker = None


@dataclass
class ContentTemplate:
    """Content template configuration."""
    name: str
    template: str
    output_format: str  # 'markdown', 'html', 'plaintext'


class ContentGenerator:
    """
    Generate affiliate content from tracked products.
    
    Features:
    - Comparison tables (Markdown/HTML)
    - "Best Under $X" roundups
    - YouTube scripts with affiliate links
    - Blog post drafts
    - SEO titles and descriptions
    - Price drop content
    """
    
    def __init__(self):
        self.partner_tag = os.getenv("AMAZON_PARTNER_TAG", "vhicklegar011-20")
        self.tracker = MultiVendorTracker() if MultiVendorTracker else None
    
    def _get_affiliate_link(self, asin: str) -> str:
        """Generate affiliate link for ASIN."""
        return f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"
    
    def generate_comparison_table(self, products: List[Dict], 
                                   format: str = "markdown") -> str:
        """
        Generate comparison table for products.
        
        Args:
            products: List of product dicts with name, price, specs, etc.
            format: 'markdown', 'html', or 'plain'
        
        Returns:
            Formatted comparison table
        """
        if format == "markdown":
            return self._markdown_table(products)
        elif format == "html":
            return self._html_table(products)
        else:
            return self._plain_table(products)
    
    def _markdown_table(self, products: List[Dict]) -> str:
        """Generate Markdown table."""
        # Headers
        headers = ["Product", "Price", "CPU", "RAM", "Best For", "Link"]
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Rows
        for p in products:
            specs = p.get('specs', {})
            price_str = f"${p.get('price', 'N/A')}" if p.get('price') else "Check Amazon"
            row = [
                p.get('name', 'Unknown'),
                price_str,
                specs.get('cpu', 'N/A'),
                specs.get('ram', 'N/A'),
                p.get('best_for', 'General'),
                f"[Buy]({p.get('affiliate_link', '#')})"
            ]
            lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(lines)
    
    def _html_table(self, products: List[Dict]) -> str:
        """Generate HTML table."""
        html = ["<table class=\"comparison-table\">"]
        html.append("<thead><tr>")
        for header in ["Product", "Price", "CPU", "RAM", "Best For", "Link"]:
            html.append(f"<th>{header}</th>")
        html.append("</tr></thead><tbody>")
        
        for p in products:
            specs = p.get('specs', {})
            price_str = f"${p.get('price', 'N/A')}" if p.get('price') else "Check Amazon"
            html.append("<tr>")
            html.append(f"<td>{p.get('name', 'Unknown')}</td>")
            html.append(f"<td>{price_str}</td>")
            html.append(f"<td>{specs.get('cpu', 'N/A')}</td>")
            html.append(f"<td>{specs.get('ram', 'N/A')}</td>")
            html.append(f"<td>{p.get('best_for', 'General')}</td>")
            html.append(f"<td><a href=\"{p.get('affiliate_link', '#')}\" class=\"btn-buy\">Buy</a></td>")
            html.append("</tr>")
        
        html.append("</tbody></table>")
        return "\n".join(html)
    
    def _plain_table(self, products: List[Dict]) -> str:
        """Generate plain text table."""
        lines = []
        lines.append("COMPARISON TABLE")
        lines.append("=" * 80)
        
        for p in products:
            specs = p.get('specs', {})
            price_str = f"${p.get('price', 'N/A')}" if p.get('price') else "Check Amazon"
            lines.append(f"\n{p.get('name', 'Unknown')}")
            lines.append(f"  Price: {price_str}")
            lines.append(f"  CPU: {specs.get('cpu', 'N/A')}")
            lines.append(f"  RAM: {specs.get('ram', 'N/A')}")
            lines.append(f"  Link: {p.get('affiliate_link', '#')}")
        
        return "\n".join(lines)
    
    def generate_roundup(self, title: str, products: List[Dict], 
                       max_price: Optional[float] = None,
                       format: str = "markdown") -> str:
        """
        Generate "Best X Under $Y" style roundup article.
        
        Args:
            title: Article title
            products: List of products to include
            max_price: Maximum price for filter
            format: Output format
        
        Returns:
            Full article content
        """
        # Filter by price if specified
        if max_price:
            products = [p for p in products if p.get('price') and p['price'] <= max_price]
        
        # Sort by price (lowest first for "best value" angle)
        products = sorted(products, key=lambda x: x.get('price', float('inf')))
        
        if format == "markdown":
            return self._markdown_roundup(title, products, max_price)
        elif format == "html":
            return self._html_roundup(title, products, max_price)
        else:
            return self._plain_roundup(title, products, max_price)
    
    def _markdown_roundup(self, title: str, products: List[Dict], 
                        max_price: Optional[float]) -> str:
        """Generate Markdown roundup."""
        lines = []
        
        # Title
        lines.append(f"# {title}")
        lines.append("")
        
        # Meta
        lines.append(f"*Last updated: {datetime.now().strftime('%B %d, %Y')}*")
        lines.append("")
        
        # Intro
        price_text = f" under ${max_price:.0f}" if max_price else ""
        lines.append(f"Looking for the best single board computers{price_text}? "
                    "We've compared the top options to help you find the perfect fit for your project.")
        lines.append("")
        lines.append("**Quick Comparison**")
        lines.append("")
        
        # Add comparison table
        lines.append(self._markdown_table(products))
        lines.append("")
        
        # Individual reviews
        lines.append("## Detailed Reviews")
        lines.append("")
        
        for i, p in enumerate(products, 1):
            specs = p.get('specs', {})
            price_str = f"${p.get('price', 'N/A')}" if p.get('price') else "Check current price"
            
            lines.append(f"### {i}. {p.get('name', 'Unknown')}")
            lines.append("")
            lines.append(f"**Price:** {price_str}")
            lines.append("")
            lines.append(f"**Specs:** {specs.get('cpu', 'N/A')} | {specs.get('ram', 'N/A')} RAM")
            lines.append("")
            lines.append(f"**Best for:** {p.get('best_for', 'General purpose projects')}")
            lines.append("")
            
            # Pros/Cons
            lines.append("**Pros:**")
            for pro in p.get('pros', ['Great value', 'Good performance']):
                lines.append(f"- {pro}")
            lines.append("")
            
            if p.get('cons'):
                lines.append("**Cons:**")
                for con in p['cons']:
                    lines.append(f"- {con}")
                lines.append("")
            
            lines.append(f"[**Check Price on Amazon →**]({p.get('affiliate_link', '#')})")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Conclusion
        lines.append("## Conclusion")
        lines.append("")
        lines.append(f"All prices and availability were accurate as of {datetime.now().strftime('%B %d, %Y')}. "
                    "Prices on Amazon fluctuate, so check the links above for current pricing.")
        lines.append("")
        lines.append("**Disclosure:** This post contains affiliate links. We earn a small commission "
                    "if you purchase through our links, at no extra cost to you.")
        
        return "\n".join(lines)
    
    def generate_youtube_script(self, product: Dict, alternatives: List[Dict]) -> Dict:
        """
        Generate YouTube video script and description.
        
        Args:
            product: Main product being reviewed
            alternatives: Similar products to compare
        
        Returns:
            Dict with script and description
        """
        title = f"{product['name']} Review & Best Alternatives"
        
        script = f"""YOUTUBE VIDEO SCRIPT: {title}

[HOOK - 0:00-0:30]
"Is the {product['name']} worth it in {datetime.now().strftime('%Y')}? 
Today I'm testing this {product.get('best_for', 'SBC')} and comparing it to {len(alternatives)} alternatives
under ${product.get('price', 200):.0f}."

[INTRO - 0:30-1:00]
- What is {product['name']}?
- Specs: {product.get('specs', {}).get('cpu', 'N/A')}, {product.get('specs', {}).get('ram', 'N/A')} RAM
- Current price: ${product.get('price', 'N/A')} (link below)

[MAIN REVIEW - 1:00-5:00]
- Unboxing
- First impressions
- Performance tests
- Use cases

[COMPARISON - 5:00-8:00]
Alternatives mentioned:"""
        
        for alt in alternatives:
            script += f"\n- {alt['name']}: ${alt.get('price', 'N/A')} [AFFILIATE_LINK]"
        
        script += f"""

[CONCLUSION - 8:00-9:00]
- Who should buy {product['name']}?
- Best alternative for budget
- Final verdict

[OUTRO - 9:00-10:00]
- Subscribe for more SBC reviews
- Links in description
- Comment your questions

---
"""
        
        description = f"""{product['name']} review and comparison with the best alternatives.

🏆 Best Overall: {product['name']} (${product.get('price', 'N/A')})
🔗 {product.get('affiliate_link', '#')}

CHAPTERS:
0:00 Intro
0:30 What is {product['name']}?
1:00 Unboxing & First Look
3:00 Performance Tests
5:00 Comparison: {product['name']} vs Alternatives
7:00 Best Alternatives
8:30 Final Verdict

ALTERNATIVES:"""
        
        for alt in alternatives:
            description += f"""
• {alt['name']} (${alt.get('price', 'N/A')}): {alt.get('affiliate_link', '#')}"""
        
        description += f"""

Disclaimer: This video contains affiliate links. 
I earn a small commission at no extra cost to you.

#SingleBoardComputer #SBC #RaspberryPiAlternative #TechReview #{product['name'].replace(' ', '')}
"""
        
        return {
            "title": title,
            "script": script,
            "description": description,
            "tags": [
                "single board computer",
                "SBC",
                product['name'],
                "tech review",
                "raspberry pi alternative"
            ]
        }
    
    def generate_price_drop_content(self, price_drops: List[Dict]) -> str:
        """Generate "Price Drop This Week" style content."""
        if not price_drops:
            return "No significant price changes this week."
        
        lines = []
        lines.append(f"# 🔥 Price Drops This Week ({datetime.now().strftime('%B %d')})")
        lines.append("")
        lines.append("Great news! Several SBCs just dropped in price:")
        lines.append("")
        
        for drop in price_drops:
            old = drop.get('old_price', 0)
            new = drop.get('new_price', 0)
            pct = drop.get('drop_percent', ((old - new) / old * 100) if old else 0)
            savings = old - new
            
            lines.append(f"## {drop['name']}")
            lines.append("")
            lines.append(f"**💰 Was:** ${old:.2f}")
            lines.append(f"**💵 Now:** ${new:.2f}")
            lines.append(f"**📉 Save:** {pct:.1f}% (${savings:.2f})")
            lines.append("")
            lines.append(f"[{drop.get('cta', 'Check Current Price →')}]({drop.get('affiliate_link', '#')})")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        lines.append("*Prices subject to change. Last updated: "
                    f"{datetime.now().strftime('%B %d, %Y at %H:%M')}*")
        
        return "\n".join(lines)
    
    def generate_seo_meta(self, title: str, description: str, 
                          keywords: List[str]) -> Dict:
        """Generate SEO-friendly meta information."""
        # Truncate to SEO-friendly lengths
        title_tag = title[:60] if len(title) <= 60 else title[:57] + "..."
        meta_desc = description[:160] if len(description) <= 160 else description[:157] + "..."
        
        return {
            "title_tag": title_tag,
            "meta_description": meta_desc,
            "keywords": keywords[:10],  # Top 10 keywords
            "og_title": title,
            "og_description": description[:200],
            "canonical_url": "",  # To be filled
            "schema_markup": self._generate_schema_json(title, description)
        }
    
    def _generate_schema_json(self, title: str, description: str) -> str:
        """Generate JSON-LD schema markup."""
        schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": title,
            "description": description,
            "author": {
                "@type": "Organization",
                "name": "ChipRadar"
            },
            "datePublished": datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat()
        }
        return json.dumps(schema, indent=2)
    
    def save_content(self, content: str, filename: str, output_dir: Optional[Path] = None):
        """Save generated content to file."""
        if output_dir is None:
            output_dir = Path.home() / ".openclaw" / "content_output"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath


def main():
    """CLI for content generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Generator v1")
    parser.add_argument("--demo", action="store_true", help="Generate sample content")
    parser.add_argument("--roundup", help="Generate roundup with title")
    parser.add_argument("--max-price", type=float, default=200, help="Max price for roundup")
    
    args = parser.parse_args()
    
    generator = ContentGenerator()
    
    if args.demo:
        print("Content Generator v1 Demo")
        print("="*60)
        
        # Sample products
        products = [
            {"name": "Radxa Rock 5C", "price": 176, "specs": {"cpu": "RK3588S2", "ram": "4GB"},
             "affiliate_link": "#", "best_for": "AI"},
            {"name": "Raspberry Pi 5", "price": 58, "specs": {"cpu": "BCM2712", "ram": "4GB"},
             "affiliate_link": "#", "best_for": "Education"},
        ]
        
        print("\nComparison Table:")
        print(generator.generate_comparison_table(products))
        
        print("\n\nRoundup: Best SBCs Under $200")
        print(generator.generate_roundup("Best SBCs Under $200", products, max_price=200))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()