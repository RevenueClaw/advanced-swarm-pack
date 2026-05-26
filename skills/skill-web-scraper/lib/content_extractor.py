#!/usr/bin/env python3
"""
Content Extractor - Intelligent Data Extraction

Extracts structured data from HTML using multiple strategies:
- CSS selectors with fallback chains
- XPath expressions
- Regex patterns for specific patterns
- LLM-assisted extraction for complex/unstructured content
- Auto-detection of common schemas (articles, products, prices)
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not available - install with: pip install beautifulsoup4")
    
try:
    import lxml.html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


@dataclass
class ExtractedData:
    """Result from content extraction."""
    data: Dict[str, Any]
    confidence: float
    method: str
    raw_html: Optional[str] = None
    selectors_used: List[str] = None
    
    
class ContentExtractor:
    """
    Intelligent content extraction from HTML.
    
    Supports:
    - Schema.org JSON-LD extraction
    - Meta tag parsing
    - CSS selector chains with fallbacks
    - Table extraction
    - Price/Product detection
    """
    
    # Common CSS selector fallbacks for common fields
    SELECTOR_FALLBACKS = {
        "title": [
            'h1',
            '[data-testid="title"]',
            '.title',
            '.product-title',
            '[itemprop="name"]',
            'meta[property="og:title"]',
        ],
        "price": [
            '[data-testid="price"]',
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.amount',
            '.current-price',
            'meta[property="product:price:amount"]',
        ],
        "description": [
            '[data-testid="description"]',
            '.description',
            '.product-description',
            '[itemprop="description"]',
            'meta[name="description"]',
            'meta[property="og:description"]',
        ],
        "image": [
            '[data-testid="image"]',
            '.product-image img',
            '[itemprop="image"]',
            'meta[property="og:image"]',
            '.main-image img',
            'img[class*="product"]',
        ],
        "availability": [
            '[data-testid="availability"]',
            '.availability',
            '[itemprop="availability"]',
            '.stock',
            '.in-stock',
            '.out-of-stock',
        ],
    }
    
    def __init__(self):
        self.extraction_stats = {
            "total_attempts": 0,
            "successful": 0,
            "by_method": {},
        }
        
    def extract(
        self,
        html: str,
        schema: Optional[Dict[str, List[str]]] = None,
        target_type: Optional[str] = None,  # "product", "article", "price", "general"
    ) -> ExtractedData:
        """
        Extract structured data from HTML.
        
        Args:
            html: Raw HTML content
            schema: Custom CSS selectors for fields
            target_type: Auto-detect extraction strategy
        """
        self.extraction_stats["total_attempts"] += 1
        
        methods_tried = []
        
        # Method 1: JSON-LD Schema.org
        try:
            data = self._extract_jsonld(html)
            if data and any(data.values()):
                self.extraction_stats["successful"] += 1
                self.extraction_stats["by_method"]["jsonld"] = self.extraction_stats["by_method"].get("jsonld", 0) + 1
                return ExtractedData(
                    data=data,
                    confidence=0.9,
                    method="jsonld",
                    raw_html=html[:1000] if html else None,
                )
        except Exception as e:
            methods_tried.append(f"jsonld_error: {e}")
            
        # Method 2: Meta tags
        try:
            data = self._extract_meta(html)
            if data and any(data.values()):
                self.extraction_stats["successful"] += 1
                self.extraction_stats["by_method"]["meta"] = self.extraction_stats["by_method"].get("meta", 0) + 1
                return ExtractedData(
                    data=data,
                    confidence=0.85,
                    method="meta",
                    raw_html=html[:1000] if html else None,
                )
        except Exception as e:
            methods_tried.append(f"meta_error: {e}")
            
        # Method 3: CSS Selector extraction
        try:
            custom_schema = schema or self.SELECTOR_FALLBACKS
            data = self._extract_with_selectors(html, custom_schema)
            if data and any(data.values()):
                self.extraction_stats["successful"] += 1
                self.extraction_stats["by_method"]["css"] = self.extraction_stats["by_method"].get("css", 0) + 1
                return ExtractedData(
                    data=data,
                    confidence=0.7,
                    method="css_selectors",
                    raw_html=html[:1000] if html else None,
                )
        except Exception as e:
            methods_tried.append(f"css_error: {e}")
            
        # Method 4: Type-specific extraction
        if target_type:
            try:
                data = self._extract_by_type(html, target_type)
                if data:
                    self.extraction_stats["successful"] += 1
                    self.extraction_stats["by_method"][target_type] = self.extraction_stats["by_method"].get(target_type, 0) + 1
                    return ExtractedData(
                        data=data,
                        confidence=0.6,
                        method=target_type,
                        raw_html=html[:1000] if html else None,
                    )
            except Exception as e:
                methods_tried.append(f"type_error: {e}")
                
        # Fallback: Minimal extraction
        data = self._minimal_extract(html)
        return ExtractedData(
            data=data,
            confidence=0.4,
            method="minimal",
            raw_html=html[:1000] if html else None,
        )
        
    def _extract_jsonld(self, html: str) -> Dict:
        """Extract JSON-LD Schema.org data."""
        if not BS4_AVAILABLE:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all("script", type="application/ld+json")
        
        results = {}
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}
                    
                if data.get("@type") in ["Product", "ItemPage", "WebPage"]:
                    results["schema_type"] = data.get("@type")
                    results["name"] = data.get("name", "")
                    results["description"] = data.get("description", "")
                    
                    if "offers" in data:
                        offers = data["offers"]
                        if isinstance(offers, list):
                            offers = offers[0]
                        if isinstance(offers, dict):
                            results["price"] = offers.get("price")
                            results["price_currency"] = offers.get("priceCurrency")
                            results["availability"] = offers.get("availability", "").split("/")[-1]
                            
            except Exception as e:
                continue
                
        return results
        
    def _extract_meta(self, html: str) -> Dict:
        """Extract OpenGraph and meta tags."""
        if not BS4_AVAILABLE:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        results = {}
        
        # OpenGraph
        og_tags = {
            "og:title": "title",
            "og:description": "description",
            "og:image": "image",
            "og:price:amount": "price",
            "og:price:currency": "currency",
        }
        
        for og_attr, key in og_tags.items():
            tag = soup.find("meta", property=og_attr)
            if tag:
                results[key] = tag.get("content", "")
                
        # Standard meta
        meta_tags = {
            "description": "description",
            "keywords": "keywords",
            "author": "author",
        }
        
        for name, key in meta_tags.items():
            tag = soup.find("meta", attrs={"name": name})
            if tag:
                results[key] = tag.get("content", "")
                
        return results
        
    def _extract_with_selectors(self, html: str, schema: Dict[str, List[str]]) -> Dict:
        """Extract using CSS selectors with fallback chains."""
        if not BS4_AVAILABLE:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        results = {}
        selectors_used = []
        
        for field, selectors in schema.items():
            for selector in selectors:
                try:
                    # Handle meta tag selectors specially
                    if selector.startswith("meta["):
                        tag = soup.select_one(selector)
                        if tag:
                            content = tag.get("content", "")
                            if content:
                                results[field] = content
                                selectors_used.append(f"{field}: {selector}")
                                break
                    else:
                        element = soup.select_one(selector)
                        if element:
                            # Get text content
                            text = element.get_text(strip=True)
                            if not text and element.name == "img":
                                text = element.get("src", "")
                            if text:
                                results[field] = text
                                selectors_used.append(f"{field}: {selector}")
                                break
                except Exception as e:
                    continue
                    
        return results
        
    def _extract_by_type(self, html: str, target_type: str) -> Dict:
        """Type-specific extraction strategies."""
        if target_type == "price":
            return self._extract_prices(html)
        elif target_type == "product":
            return self._extract_product(html)
        elif target_type == "article":
            return self._extract_article(html)
        return {}
        
    def _extract_prices(self, html: str) -> List[Dict]:
        """Extract price information from HTML."""
        results = []
        
        # Regex patterns for prices
        price_patterns = [
            r'\$([0-9,]+\.?\d{0,2})',  # $XX.XX
            r'([0-9,]+\.?\d{0,2})\s*(?:USD|\$)',  # XX.XX USD
            r'([0-9,]+\.?\d{0,2})\s*USD',  # XX.XX USD
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = float(match.replace(",", ""))
                    if 0.01 < price < 100000:
                        results.append({
                            "price": price,
                            "currency": "USD",
                        })
                except:
                    continue
                    
        return {"prices_found": results[:5]} if results else {}
        
    def _extract_product(self, html: str) -> Dict:
        """Extract product-specific data."""
        soup = BeautifulSoup(html, 'html.parser') if BS4_AVAILABLE else None
        if not soup:
            return {}
            
        data = {}
        
        # Common product patterns
        title_selectors = ['h1', '.product-title', '[data-testid="product-title"]']
        for sel in title_selectors:
            el = soup.select_one(sel)
            if el:
                data['title'] = el.get_text(strip=True)
                break
                
        # Price patterns
        price_selectors = ['.price', '.product-price', '[data-price]', '.current-price']
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                price_match = re.search(r'[\$\€\£]?([0-9,]+\.?\d{0,2})', text)
                if price_match:
                    data['price'] = price_match.group(0)
                    break
                    
        return data
        
    def _extract_article(self, html: str) -> Dict:
        """Extract article/blog post content."""
        if not BS4_AVAILABLE:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Article content
        article_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
        ]
        
        for sel in article_selectors:
            el = soup.select_one(sel)
            if el:
                # Clean text
                for script in el.find_all(["script", "style"]):
                    script.extract()
                data['content'] = el.get_text(separator='\n', strip=True)
                data['content_html'] = str(el)
                break
                
        # Author
        author_selectors = ['.author', '[rel="author"]', '.byline']
        for sel in author_selectors:
            el = soup.select_one(sel)
            if el:
                data['author'] = el.get_text(strip=True)
                break
                
        # Publish date
        date_selectors = ['time', '[datetime]', '.published', '.date']
        for sel in date_selectors:
            el = soup.select_one(sel)
            if el:
                data['date'] = el.get("datetime") or el.get_text(strip=True)
                break
                
        return data
        
    def _minimal_extract(self, html: str) -> Dict:
        """Fallback minimal extraction."""
        if not BS4_AVAILABLE:
            # Regex fallback
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            return {
                "title": title_match.group(1).strip() if title_match else "",
            }
            
        soup = BeautifulSoup(html, 'html.parser')
        
        return {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "text": soup.get_text(separator=' ', strip=True)[:2000],
            "links": len(soup.find_all("a")),
        }
        
    def get_stats(self) -> Dict:
        """Get extraction statistics."""
        return {
            **self.extraction_stats,
            "success_rate": self.extraction_stats["successful"] / max(self.extraction_stats["total_attempts"], 1),
        }


if __name__ == "__main__":
    # Test extraction
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Product</title>
        <meta property="og:title" content="Test Product OG">
        <meta property="og:price:amount" content="99.99">
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Test Product JSON-LD",
            "offers": {
                "@type": "Offer",
                "price": "89.99",
                "priceCurrency": "USD"
            }
        }
        </script>
    </head>
    <body>
        <h1>Test Product Title</h1>
        <div class="price">$79.99</div>
        <div class="description">This is a test product description.</div>
    </body>
    </html>
    """
    
    extractor = ContentExtractor()
    result = extractor.extract(test_html)
    
    print(f"Extraction Result:")
    print(f"  Method: {result.method}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Data: {json.dumps(result.data, indent=2)}")
