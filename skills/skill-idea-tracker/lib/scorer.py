#!/usr/bin/env python3
"""
Idea Scorer - 5D Scoring Framework

Revenue: 35%
Effort: 20% (lower effort = higher score)
AI Relevance: 25%
Strategic Fit: 20%

v1.0.1 - Production Release
"""

import sys
import re
from pathlib import Path
from typing import Dict

# Handle both relative and absolute imports
try:
    from .idea_tracker import Idea, ScoreResult
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from idea_tracker import Idea, ScoreResult


class IdeaScorer:
    """Score business ideas on 5 dimensions."""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'revenue': 0.35,
            'effort': 0.20,
            'ai_relevance': 0.25,
            'strategic_fit': 0.20
        }
    
    def score(self, idea: Idea) -> ScoreResult:
        """
        Calculate 5D score for an idea.
        
        Returns:
            ScoreResult with all dimensions
        """
        # Revenue score (logarithmic scale, max at $50K/mo)
        revenue_score = self._score_revenue(idea.revenue_monthly)
        
        # Effort score (inverse, lower effort = higher score)
        effort_score = self._score_effort(idea.effort_level)
        
        # AI relevance score
        ai_relevance = self._score_ai_relevance(
            idea.name + ' ' + idea.description
        )
        
        # Strategic fit (based on description/source patterns)
        strategic_fit = self._score_strategic_fit(idea)
        
        # Calculate weighted total
        total = int(
            revenue_score * self.weights['revenue'] +
            effort_score * self.weights['effort'] +
            ai_relevance * self.weights['ai_relevance'] +
            strategic_fit * self.weights['strategic_fit']
        )
        
        # Confidence based on data completeness
        confidence = 0.7  # Base
        if idea.revenue_monthly > 0:
            confidence += 0.2
        if 'ai' in idea.name.lower() or 'automation' in idea.name.lower():
            confidence += 0.1
        confidence = min(confidence, 1.0)
        
        return ScoreResult(
            revenue_score=revenue_score,
            effort_score=effort_score,
            ai_relevance=ai_relevance,
            strategic_fit=strategic_fit,
            total_score=total,
            confidence=round(confidence, 2)
        )
    
    def _score_revenue(self, revenue: int) -> int:
        """
        Score revenue potential.
        Logarithmic scale: $1K=40, $5K=60, $10K=75, $50K=100
        """
        if revenue <= 0:
            return 30  # Unknown
        
        import math
        # Cap at $50K for max score
        capped = min(revenue, 50000)
        score = int(30 + 70 * math.log(capped / 1000 + 1) / math.log(51))
        return min(score, 100)
    
    def _score_effort(self, effort: str) -> int:
        """Score effort (inverse: lower effort = higher score)."""
        scores = {
            'Low': 90,
            'Medium': 65,
            'High': 40
        }
        return scores.get(effort, 50)
    
    def _score_ai_relevance(self, text: str) -> int:
        """Score AI/agent alignment."""
        text = text.lower()
        
        high_keywords = ['AI', 'automation', 'software', 'digital', 
                        'virtual assistant', 'chatbot', 'LLM', 'agent']
        medium_keywords = ['online', 'website', 'content', 'service', 'consulting']
        low_keywords = ['physical', 'retail', 'warehouse', 'storefront']
        
        score = 50  # Baseline
        
        for kw in high_keywords:
            if kw.lower() in text:
                score += 8
        
        for kw in medium_keywords:
            if kw.lower() in text:
                score += 4
        
        for kw in low_keywords:
            if kw.lower() in text:
                score -= 10
        
        return min(max(score, 0), 100)
    
    def _score_strategic_fit(self, idea: Idea) -> int:
        """Score alignment with current resources/skills."""
        text = (idea.name + ' ' + idea.description).lower()
        score = 60  # Baseline
        
        # Boost for software/tech (matches current capabilities)
        if any(kw in text for kw in ['software', 'app', 'platform', 'SaaS', 'API']):
            score += 15
        
        # Boost for automation (current strength)
        if any(kw in text for kw in ['automation', 'workflow', 'no-code', 'low-code']):
            score += 10
        
        # Penalty for things requiring physical presence
        if any(kw in text for kw in ['storefront', 'warehouse', 'delivery', 'physical']):
            score -= 15
        
        # Boost for low startup cost
        if idea.startup_cost == 'Low':
            score += 10
        
        return min(max(score, 0), 100)


# Self-verification
if __name__ == "__main__":
    try:
        from .idea_tracker import Idea
    except ImportError:
        from idea_tracker import Idea
    
    scorer = IdeaScorer()
    
    # Test case: High-value AI automation
    idea = Idea(
        id="test1",
        source="Side Hustle Nation",
        name="AI Service Bot Automation",
        description="Build AI-powered service bot for customer support",
        revenue_monthly=15000,
        startup_cost="Low",
        effort_level="Medium",
        extracted_at="2026-05-24"
    )
    
    score = scorer.score(idea)
    print(f"High-value AI idea score: {score.total_score}")
    print(f"  Revenue: {score.revenue_score}")
    print(f"  AI Relevance: {score.ai_relevance}")
    
    assert score.total_score > 70, "High-value AI idea should score > 70"
    
    # Test case: Low-value physical
    idea2 = Idea(
        id="test2",
        source="Newsletter",
        name="Pizza Delivery Service",
        description="Start local pizza delivery business",
        revenue_monthly=3000,
        startup_cost="High",
        effort_level="High",
        extracted_at="2026-05-24"
    )
    
    score2 = scorer.score(idea2)
    print(f"\nPhysical business score: {score2.total_score}")
    print(f"  Revenue: {score2.revenue_score}")
    print(f"  AI Relevance: {score2.ai_relevance}")
    
    assert score2.total_score < 60, "Physical business should score < 60"
    
    print("\n✓ All scoring tests passed")
