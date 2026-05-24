#!/usr/bin/env python3
"""
Newsletter Processor - Extract business ideas from newsletters.

Integrates with income-automation-audit to capture opportunities.

Author: RockClaw
Version: 1.0.0
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


try:
    from agentmail import AgentMail
    AGENTMAIL_AVAILABLE = True
except ImportError:
    AGENTMAIL_AVAILABLE = False


@dataclass
class BusinessIdea:
    """Extracted business opportunity."""
    source: str
    subject: str
    date: str
    name: str
    idea_type: str
    revenue_potential: str
    startup_cost: str
    description: str
    relevance: str  # HIGH, MEDIUM, LOW
    extracted_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class NewsletterProcessor:
    """
    Process newsletters from AgentMail inbox and extract business ideas.
    
    Usage:
        processor = NewsletterProcessor()
        ideas = processor.process_newsletters(since_days=7)
        processor.save_ideas(ideas)
    """
    
    # Known newsletter sources and their idea patterns
    NEWSLETTER_SOURCES = {
        'nick@sidehustlenation.com': {
            'name': 'Side Hustle Nation',
            'patterns': [
                (r'\$(\d{1,3}(?:,\d{3})*)(?:\/mo| per month| a month)', 'revenue_pattern'),
                (r'(\d{1,3}(?:,\d{3})*) (?:items|sales|customers)', 'volume_pattern'),
                (r'in (\d+) months?', 'timeline_pattern'),
            ]
        }
    }
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".openclaw/workspace/newsletter-ideas"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.ideas_file = self.storage_path / "extracted-ideas.jsonl"
        self.summary_file = self.storage_path / "ideas-summary.json"
        
        self.client = None
        if AGENTMAIL_AVAILABLE:
            api_key = os.getenv('AGENTMAIL_API_KEY')
            if api_key:
                self.client = AgentMail(api_key=api_key)
    
    def process_newsletters(self, since_days: int = 7, inbox_id: str = 'revenueclaw@agentmail.to') -> List[BusinessIdea]:
        """
        Fetch and process recent newsletters.
        
        Args:
            since_days: Only process newsletters from last N days
            inbox_id: AgentMail inbox to check
            
        Returns:
            List of extracted BusinessIdea objects
        """
        if not self.client:
            print("Warning: AgentMail client not available")
            return []
        
        ideas = []
        messages = self.client.inboxes.messages.list(inbox_id=inbox_id, limit=50)
        
        for msg in messages.messages:
            sender = str(msg.from_) if msg.from_ else ''
            subject = msg.subject or ''
            
            # Only process known newsletter sources
            for source_email, config in self.NEWSLETTER_SOURCES.items():
                if source_email in sender.lower():
                    # Get full message content
                    full_msg = self.client.inboxes.messages.get(
                        inbox_id=inbox_id, 
                        message_id=msg.message_id
                    )
                    content = full_msg.text or full_msg.html or ''
                    
                    # Extract idea
                    idea = self._extract_idea(subject, content, config['name'], msg.created_at)
                    if idea:
                        ideas.append(idea)
        
        return ideas
    
    def _extract_idea(self, subject: str, content: str, source_name: str, date) -> Optional[BusinessIdea]:
        """Extract business idea from newsletter content."""
        
        # Skip sponsored messages, ads, etc
        if any(skip in subject.lower() for skip in ['sponsored', 'ad:', 'advertisement']):
            return None
        
        # Determine relevance based on keywords
        relevance = self._assess_relevance(subject, content)
        
        # Extract revenue numbers
        revenue = self._extract_revenue(subject, content)
        
        # Extract business type/name
        idea_name = self._extract_idea_name(subject, content)
        
        # Determine startup cost based on content
        startup_cost = self._assess_startup_cost(content)
        
        # Generate description
        description = self._generate_description(content)
        
        return BusinessIdea(
            source=source_name,
            subject=subject,
            date=str(date)[:10],
            name=idea_name,
            idea_type=self._classify_type(subject, content),
            revenue_potential=revenue,
            startup_cost=startup_cost,
            description=description,
            relevance=relevance,
            extracted_at=datetime.now().isoformat()
        )
    
    def _assess_relevance(self, subject: str, content: str) -> str:
        """Assess how relevant this idea is to our AI/agent focus."""
        high_keywords = ['AI', 'automation', 'software', 'digital', 'virtual', 'assistant', 'data']
        medium_keywords = ['service', 'consulting', 'freelance', 'content', 'website']
        
        text = (subject + ' ' + content[:2000]).lower()
        
        high_score = sum(1 for kw in high_keywords if kw.lower() in text)
        medium_score = sum(1 for kw in medium_keywords if kw.lower() in text)
        
        if high_score >= 2:
            return 'HIGH'
        elif high_score >= 1 or medium_score >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _extract_revenue(self, subject: str, content: str) -> str:
        """Extract revenue potential from content."""
        # Look for dollar amounts
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)(?:\/mo| per month| a month|/month)',
            r'\$(\d{1,3}(?:,\d{3})*)(?:k|K)',
            r'(\$\d{1,3}(?:,\d{3})*) per',
        ]
        
        text = subject + ' ' + content[:3000]
        revenues = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            revenues.extend(matches)
        
        if revenues:
            return f"{revenues[0]}/mo potential"
        return 'Unknown'
    
    def _extract_idea_name(self, subject: str, content: str) -> str:
        """Extract a name for this business idea."""
        # Use subject as base
        name = subject.replace('Side hustle idea 💡:', '').strip()
        name = name.replace('Side hustle:', '').strip()
        
        # Look for specific business mentions
        if 'AI' in name or 'assistant' in name.lower():
            return 'AI Service Business'
        elif 'website' in name.lower():
            return 'Website Development Service'
        elif 'slumber' in name.lower() or 'sleepover' in name.lower():
            return 'Event Setup Service'
        
        return name[:50] if name else 'Business Opportunity'
    
    def _assess_startup_cost(self, content: str) -> str:
        """Estimate startup cost from content."""
        low_indicators = ['free', '$0', 'no cost', 'minimal']
        high_indicators = ['inventory', 'equipment', 'storefront', 'warehouse']
        
        text = content.lower()[:2000]
        
        low_score = sum(1 for ind in low_indicators if ind in text)
        high_score = sum(1 for ind in high_indicators if ind in text)
        
        if low_score >= 2:
            return 'Low ($0-500)'
        elif high_score >= 2:
            return 'High ($5,000+)'
        else:
            return 'Medium ($500-5,000)'
    
    def _classify_type(self, subject: str, content: str) -> str:
        """Classify the business type."""
        text = (subject + ' ' + content[:1000]).lower()
        
        if any(word in text for word in ['ai', 'automation', 'software', 'app', 'platform']):
            return 'Technology/AI'
        elif any(word in text for word in ['service', 'consulting', 'freelance']):
            return 'Service'
        elif any(word in text for word in ['product', 'sell', 'ecommerce', 'shopify']):
            return 'E-commerce/Product'
        elif any(word in text for word in ['content', 'writing', 'blog', 'youtube']):
            return 'Content Creation'
        else:
            return 'Service'
    
    def _generate_description(self, content: str) -> str:
        """Generate brief description from content."""
        # Get first substantial paragraph
        paragraphs = content.split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if len(p) > 50 and not p.startswith('http'):
                return p[:200] + '...' if len(p) > 200 else p
        return 'Business opportunity from newsletter'
    
    def save_ideas(self, ideas: List[BusinessIdea]):
        """Save extracted ideas to storage."""
        # Append to JSONL
        with open(self.ideas_file, 'a') as f:
            for idea in ideas:
                f.write(json.dumps(idea.to_dict()) + '\n')
        
        # Update summary
        self._update_summary(ideas)
    
    def _update_summary(self, new_ideas: List[BusinessIdea]):
        """Update summary statistics."""
        summary = {
            'last_updated': datetime.now().isoformat(),
            'total_ideas_extracted': 0,
            'high_relevance_count': 0,
            'by_source': {},
            'recent_ideas': []
        }
        
        # Load existing
        if self.summary_file.exists():
            with open(self.summary_file) as f:
                summary = json.load(f)
        
        # Update counts
        summary['total_ideas_extracted'] += len(new_ideas)
        summary['high_relevance_count'] += sum(1 for i in new_ideas if i.relevance == 'HIGH')
        summary['last_updated'] = datetime.now().isoformat()
        
        # Update sources
        for idea in new_ideas:
            source = idea.source
            summary['by_source'][source] = summary['by_source'].get(source, 0) + 1
        
        # Recent ideas (keep last 20)
        recent = [i.to_dict() for i in new_ideas]
        summary['recent_ideas'] = recent + summary.get('recent_ideas', [])
        summary['recent_ideas'] = summary['recent_ideas'][:20]
        
        # Save
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def get_summary(self) -> Dict:
        """Get summary of all extracted ideas."""
        if self.summary_file.exists():
            with open(self.summary_file) as f:
                return json.load(f)
        return {}
    
    def get_high_relevance_ideas(self, limit: int = 10) -> List[Dict]:
        """Get high-relevance ideas for review."""
        high_ideas = []
        
        if self.ideas_file.exists():
            with open(self.ideas_file) as f:
                for line in f:
                    idea = json.loads(line)
                    if idea.get('relevance') == 'HIGH':
                        high_ideas.append(idea)
        
        return sorted(high_ideas, key=lambda x: x.get('date', ''), reverse=True)[:limit]


# Integration with income audit
def run_newsletter_processing():
    """
    Run newsletter processing - designed to be called by cron job.
    """
    processor = NewsletterProcessor()
    
    # Process newsletters from last 7 days
    ideas = processor.process_newsletters(since_days=7)
    
    if ideas:
        processor.save_ideas(ideas)
        
        # Print summary for logging
        print(f"\n=== Newsletter Processing Complete ===")
        print(f"Extracted {len(ideas)} business ideas")
        
        high_count = sum(1 for i in ideas if i.relevance == 'HIGH')
        if high_count > 0:
            print(f"⚡ {high_count} HIGH relevance ideas found!")
            
            # Show high-relevance ideas
            for idea in ideas:
                if idea.relevance == 'HIGH':
                    print(f"\n  💡 {idea.name}")
                    print(f"     Revenue: {idea.revenue_potential}")
                    print(f"     Source: {idea.source} ({idea.date})")
    else:
        print("No new business ideas found in newsletters")
    
    return ideas


if __name__ == "__main__":
    run_newsletter_processing()