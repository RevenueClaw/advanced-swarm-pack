#!/usr/bin/env python3
"""
Idea Tracker Core Module
Business opportunity pipeline with swarm integration.

v1.0.1 - Production Release
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Attempt imports for swarm integrations
try:
    from .scorer import IdeaScorer
    from .backlog_manager import BacklogManager
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False


class EffortLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class IdeaStatus(Enum):
    NEW = "new"
    SCORED = "scored"
    TASKED = "tasked"
    PURSUED = "pursued"
    REJECTED = "rejected"
    STALLED = "stalled"


@dataclass
class ScoreResult:
    """5D scoring result."""
    revenue_score: int      # 0-100, based on monthly potential
    effort_score: int       # 0-100, lower is better
    ai_relevance: int       # 0-100, AI/agent alignment
    strategic_fit: int      # 0-100, resource/skill match
    total_score: int        # Weighted composite
    confidence: float       # Scoring confidence 0-1


@dataclass
class TaskPriority:
    """Task priority levels."""
    P0 = "P0"    # $5000+/mo - Immediate attention
    P1 = "P1"    # $2000-5000/mo - High priority
    P2 = "P2"    # $1000-2000/mo - Normal priority
    P3 = "P3"    # <$1000/mo - Low priority


@dataclass
class Idea:
    """Business opportunity data model."""
    id: str
    source: str
    name: str
    description: str
    revenue_monthly: int    # Estimated monthly revenue
    startup_cost: str       # Low/Medium/High
    effort_level: str        # Low/Medium/High
    effort_hours: Optional[int] = None  # Estimated hours
    
    # Scoring (populated after scoring)
    score: Optional[ScoreResult] = None
    
    # Tracking
    status: str = "new"
    task_id: Optional[str] = None
    task_priority: Optional[str] = None
    
    # Metadata
    source_url: Optional[str] = None
    source_id: Optional[str] = None  # Email ID, job ID, etc.
    extracted_at: str = ""
    pursued_at: Optional[str] = None
    rejected_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Outcome tracking (for preference learning)
    actual_revenue: Optional[int] = None
    actual_hours: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Idea":
        if data.get('score'):
            data['score'] = ScoreResult(**data['score'])
        return cls(**data)


@dataclass
class ProcessingReport:
    """Report of processing run."""
    processed_sources: List[str]
    ideas_found: int
    ideas_scored: int
    tasks_created: int
    p0_ideas: List[Idea]
    p1_ideas: List[Idea]
    errors: List[str]
    duration_seconds: float
    
    def summary(self) -> str:
        lines = [
            "=" * 60,
            "💡 IDEA TRACKER PROCESSING REPORT",
            "=" * 60,
            f"",
            f"Sources processed: {', '.join(self.processed_sources)}",
            f"Ideas found: {self.ideas_found}",
            f"Ideas scored: {self.ideas_scored}",
            f"Tasks created: {self.tasks_created}",
            f"Duration: {self.duration_seconds:.1f}s",
            f"",
        ]
        
        if self.p0_ideas:
            lines.append("🚨 NEW P0 IDEAS (Immediate attention):")
            for idea in self.p0_ideas:
                lines.append(f"  🔴 {idea.name} - ${idea.revenue_monthly:,}/mo")
            lines.append(f"")
        
        if self.p1_ideas:
            lines.append("💎 NEW P1 IDEAS (High priority):")
            for idea in self.p1_ideas:
                lines.append(f"  🟠 {idea.name} - ${idea.revenue_monthly:,}/mo")
            lines.append(f"")
        
        if self.errors:
            lines.append("⚠️  Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        
        lines.append(f"Total high-value: {len(self.p0_ideas) + len(self.p1_ideas)}")
        lines.append("=" * 60)
        
        return '\n'.join(lines)


class IdeaTracker:
    """
    Business opportunity tracker with swarm integration.
    
    Usage:
        tracker = IdeaTracker()
        
        # Process all sources
        report = tracker.process_all()
        
        # View backlog
        backlog = tracker.get_prioritized_backlog(min_score=70)
    """
    
    DEFAULT_CONFIG = {
        'task_creation_threshold': {
            'revenue_monthly': 1000,
            'ai_relevance': 50,
            'effort_max': 'High',
            'min_score': 60
        },
        'scoring_weights': {
            'revenue': 0.35,
            'effort': 0.20,
            'ai_relevance': 0.25,
            'strategic_fit': 0.20
        },
        'auto_cleanup': True,
        'archive_enabled': True,
        'notify_on_p0': True,
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.workspace = Path.home() / ".openclaw/workspace/idea-tracker"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.backlog_dir = self.workspace / "backlog"
        self.backlog_dir.mkdir(exist_ok=True)
        
        self.sources_dir = self.workspace / "sources"
        self.sources_dir.mkdir(exist_ok=True)
        
        self.reports_dir = self.workspace / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load config
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.scorer = IdeaScorer(self.config['scoring_weights'])
        self.backlog = BacklogManager(self.backlog_dir)
    
    def process_source(self, source: str, since_days: int = 7, 
                      dry_run: bool = False) -> ProcessingReport:
        """
        Process a single source for ideas.
        
        Args:
            source: One of 'agentmail', 'abund', 'manual', 'all'
            since_days: Lookback period
            dry_run: If True, don't create tasks
            
        Returns:
            ProcessingReport
        """
        ideas = []
        errors = []
        
        # Source-specific extraction
        if source == "agentmail" or source == "all":
            try:
                ideas.extend(self._extract_agentmail(since_days))
            except Exception as e:
                errors.append(f"AgentMail extraction failed: {e}")
        
        if source == "abund" or source == "all":
            # Placeholder for abund.ai integration
            pass
        
        if source == "manual" or source == "all":
            # Manual entries from file
            ideas.extend(self._extract_manual())
        
        # Score and track
        scored = []
        tasks_created = 0
        p0_ideas = []
        p1_ideas = []
        
        for idea in ideas:
            if self.backlog.is_tracked(idea.id):
                continue
            
            # Score
            idea.score = self.scorer.score(idea)
            idea.status = "scored"
            
            # Store
            self.backlog.add_idea(idea)
            scored.append(idea)
            
            # Determine task priority
            priority = self._determine_priority(idea)
            
            if priority:
                idea.task_priority = priority
                
                if not dry_run:
                    task_id = self._create_task(idea)
                    if task_id:
                        idea.task_id = task_id
                        idea.status = "tasked"
                        tasks_created += 1
                
                if priority == TaskPriority.P0:
                    p0_ideas.append(idea)
                elif priority == TaskPriority.P1:
                    p1_ideas.append(idea)
        
        return ProcessingReport(
            processed_sources=[source],
            ideas_found=len(ideas),
            ideas_scored=len(scored),
            tasks_created=tasks_created,
            p0_ideas=p0_ideas,
            p1_ideas=p1_ideas,
            errors=errors,
            duration_seconds=0.0  # Would track actual time
        )
    
    def process_all(self, since_days: int = 7, dry_run: bool = False) -> ProcessingReport:
        """Process all configured sources."""
        return self.process_source("all", since_days, dry_run)
    
    def add_idea(self, name: str, description: str, revenue_monthly: int,
                startup_cost: str = "Medium", effort_level: str = "Medium",
                source: str = "manual") -> Idea:
        """
        Manually add an idea.
        
        Returns:
            The created Idea
        """
        idea = Idea(
            id=self._generate_id(f"{source}_{name}_{datetime.now().isoformat()}"),
            source=source,
            name=name,
            description=description,
            revenue_monthly=revenue_monthly,
            startup_cost=startup_cost,
            effort_level=effort_level,
            extracted_at=datetime.now().isoformat()
        )
        
        # Score and track
        idea.score = self.scorer.score(idea)
        idea.status = "scored"
        self.backlog.add_idea(idea)
        
        # Create task if high-value
        priority = self._determine_priority(idea)
        if priority:
            idea.task_priority = priority
            task_id = self._create_task(idea)
            if task_id:
                idea.task_id = task_id
                idea.status = "tasked"
        
        return idea
    
    def get_prioritized_backlog(self, min_score: int = 60,
                                max_effort: str = "High",
                                status: Optional[str] = None) -> List[Idea]:
        """
        Get prioritized list of ideas.
        
        Args:
            min_score: Minimum total score (0-100)
            max_effort: Maximum effort level to include
            status: Filter by status (optional)
            
        Returns:
            List of Idea sorted by score descending
        """
        ideas = self.backlog.get_all_ideas()
        
        # Filter
        filtered = []
        for idea in ideas:
            if idea.score and idea.score.total_score >= min_score:
                # Effort filter
                effort_order = {"Low": 1, "Medium": 2, "High": 3}
                if effort_order.get(idea.effort_level, 3) <= effort_order.get(max_effort, 3):
                    if not status or idea.status == status:
                        filtered.append(idea)
        
        # Sort by score
        filtered.sort(key=lambda x: x.score.total_score if x.score else 0, reverse=True)
        
        return filtered
    
    def show_backlog(self, top_n: int = 10, min_score: int = 60):
        """Print prioritized backlog to stdout."""
        backlog = self.get_prioritized_backlog(min_score=min_score)
        
        print("=" * 70)
        print("💎 PRIORITIZED IDEA BACKLOG")
        print("=" * 70)
        print(f"\nShowing top {min(top_n, len(backlog))} ideas (min score: {min_score}):\n")
        
        for i, idea in enumerate(backlog[:top_n], 1):
            score = idea.score.total_score if idea.score else 0
            revenue = f"${idea.revenue_monthly:,}/mo" if idea.revenue_monthly else "Unknown"
            
            # Priority icon
            if idea.task_priority == TaskPriority.P0:
                icon = "🔴 P0"
            elif idea.task_priority == TaskPriority.P1:
                icon = "🟠 P1"
            elif idea.task_priority == TaskPriority.P2:
                icon = "🟡 P2"
            else:
                icon = "🟢 P3"
            
            print(f"{i}. {icon} {idea.name} (Score: {score})")
            print(f"   Source: {idea.source}")
            print(f"   Revenue: {revenue}")
            print(f"   Effort: {idea.effort_level}")
            print(f"   Status: {idea.status}")
            if idea.task_id:
                print(f"   Task ID: {idea.task_id}")
            print()
        
        if len(backlog) > top_n:
            print(f"... and {len(backlog) - top_n} more ideas")
        
        print(f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
    
    def record_outcome(self, idea_id: str, outcome: str,
                      actual_revenue: Optional[int] = None,
                      actual_hours: Optional[int] = None,
                      rejection_reason: Optional[str] = None):
        """
        Record outcome for preference learning.
        
        Args:
            idea_id: Idea ID
            outcome: pursued, rejected, stalled
            actual_revenue: Actual monthly revenue achieved
            actual_hours: Actual hours invested
            rejection_reason: Why rejected (optional)
        """
        idea = self.backlog.get_idea(idea_id)
        if not idea:
            raise ValueError(f"Idea {idea_id} not found")
        
        idea.status = outcome
        
        if outcome == "pursued":
            idea.pursued_at = datetime.now().isoformat()
            idea.actual_revenue = actual_revenue
            idea.actual_hours = actual_hours
        elif outcome == "rejected":
            idea.rejected_at = datetime.now().isoformat()
            idea.rejection_reason = rejection_reason
        
        self.backlog.update_idea(idea)
        
        # Update preference learning
        self._update_preferences(idea)
    
    # -- Internal Methods --
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration."""
        if config_path and config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        
        # Try default location
        default = Path.home() / ".openclaw/config/idea-tracker.yaml"
        if default.exists():
            import yaml
            with open(default) as f:
                return yaml.safe_load(f)
        
        return self.DEFAULT_CONFIG.copy()
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID."""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _extract_agentmail(self, since_days: int) -> List[Idea]:
        """Extract ideas from AgentMail inbox."""
        ideas = []
        
        # Try to import agentmail
        try:
            from agentmail import AgentMail
        except ImportError:
            return ideas
        
        api_key = os.getenv('AGENTMAIL_API_KEY')
        if not api_key:
            return ideas
        
        client = AgentMail(api_key=api_key)
        inbox_id = os.getenv('AGENTMAIL_INBOX_ID', 'revenueclaw@agentmail.to')
        
        try:
            messages = client.inboxes.messages.list(
                inbox_id=inbox_id,
                limit=100
            )
            
            for msg in messages.messages:
                # Check if already processed
                if self._is_agentmail_processed(msg.message_id):
                    continue
                
                # Try to extract idea
                idea = self._parse_email_to_idea(msg)
                
                if idea:
                    ideas.append(idea)
                    self._mark_agentmail_processed(msg.message_id)
                    
        except Exception as e:
            print(f"Error extracting from AgentMail: {e}")
        
        return ideas
    
    def _parse_email_to_idea(self, msg) -> Optional[Idea]:
        """Parse an email into an Idea."""
        subject = msg.subject or ''
        sender = str(msg.from_) if msg.from_ else ''
        
        # Known newsletter sources
        newsletter_sources = {
            'nick@sidehustlenation.com': 'Side Hustle Nation',
            'noreply@substack.com': 'Substack',
        }
        
        # Check if from known source
        source_name = 'Email'
        for email, name in newsletter_sources.items():
            if email in sender.lower():
                source_name = name
                break
        
        # Parse revenue patterns
        revenue = self._parse_revenue(subject + ' ' + (msg.text or ''))
        
        # Skip if no revenue indicator and not from good source
        if revenue < 500 and 'side hustle' not in subject.lower():
            return None
        
        # Classify effort
        effort = self._classify_effort(msg.text or '')
        
        # Classify startup cost
        cost = self._classify_startup_cost(msg.text or '')
        
        return Idea(
            id=self._generate_id(f"{msg.message_id}_{subject}"),
            source=source_name,
            name=subject[:60] or 'Business Opportunity',
            description=msg.text[:300] if msg.text else 'No description',
            revenue_monthly=revenue,
            startup_cost=cost,
            effort_level=effort,
            source_id=msg.message_id,
            extracted_at=datetime.now().isoformat()
        )
    
    def _extract_manual(self) -> List[Idea]:
        """Load manual idea entries."""
        manual_file = self.workspace / "manual-entries.jsonl"
        ideas = []
        
        if not manual_file.exists():
            return ideas
        
        with open(manual_file) as f:
            for line in f:
                data = json.loads(line)
                if not self.backlog.is_tracked(data.get('id', '')):
                    ideas.append(Idea.from_dict(data))
        
        return ideas
    
    def _parse_revenue(self, text: str) -> int:
        """Parse monthly revenue from text."""
        import re
        text = text.lower()
        
        patterns = [
            r'\$?(\d{1,3}(?:,\d{3})+)\s*/\s*mo',
            r'\$?(\d+(?:\.\d+)?)\s*k\s*(?:/|per)\s*mo',
            r'\$?(\d+)\s*thousand\s*per\s*month',
            r'(\$\d{1,3}(?:,\d{3})+).*month',
            r'earns?\s+\$?(\d{1,3}(?:,\d{3})+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                val = match.group(1).replace(',', '').replace('k', '')
                if 'k' in text.lower() and 'k' not in val:
                    return int(float(val) * 1000)
                return int(val)
        
        return 0
    
    def _classify_effort(self, text: str) -> str:
        """Classify effort level from text."""
        text = text.lower()
        
        # High effort indicators
        if any(word in text for word in ['full-time', '40+ hours', 'quit job', 'investment heavy']):
            return "High"
        
        # Low effort indicators
        if any(word in text for word in ['passive income', 'automation', 'runs itself', 'low maintenance']):
            return "Low"
        
        return "Medium"
    
    def _classify_startup_cost(self, text: str) -> str:
        """Classify startup cost from text."""
        text = text.lower()
        
        if any(word in text for word in ['free', '$0', 'no cost', 'minimal investment']):
            return "Low"
        
        if any(word in text for word in ['equipment', 'warehouse', 'storefront', 'inventory heavy']):
            return "High"
        
        return "Medium"
    
    def _determine_priority(self, idea: Idea) -> Optional[str]:
        """
        Determine if idea warrants task creation.
        Returns priority level or None if below threshold.
        """
        config = self.config['task_creation_threshold']
        
        # Check thresholds
        if idea.revenue_monthly < config['revenue_monthly']:
            return None
        
        if idea.score and idea.score.ai_relevance < config['ai_relevance']:
            return None
        
        effort_order = {"Low": 1, "Medium": 2, "High": 3}
        if effort_order.get(idea.effort_level, 3) > effort_order.get(config['effort_max'], 3):
            return None
        
        # Determine priority tier
        if idea.revenue_monthly >= 5000:
            return TaskPriority.P0
        elif idea.revenue_monthly >= 2000:
            return TaskPriority.P1
        elif idea.revenue_monthly >= 1000:
            return TaskPriority.P2
        else:
            return TaskPriority.P3
    
    def _create_task(self, idea: Idea) -> Optional[str]:
        """
        Create task in task-manager.
        Returns task ID or None.
        """
        # Find task-manager
        task_manager = Path.home() / ".openclaw/workspace/skills/task-manager/task-manager.py"
        if not task_manager.exists():
            return None
        
        # Determine tags
        tags = ["income-opportunity", idea.source.lower().replace(' ', '-')]
        if 'ai' in idea.name.lower() or idea.score.ai_relevance > 70:
            tags.append("ai-focused")
        
        title = f"[Income Oppty] {idea.name}"
        desc = f"""Source: {idea.source}
Revenue Potential: ${idea.revenue_monthly:,}/mo
Startup Cost: {idea.startup_cost}
Effort Level: {idea.effort_level}
AI Relevance Score: {idea.score.ai_relevance if idea.score else 'N/A'}
Total Score: {idea.score.total_score if idea.score else 'N/A'}

Description:
{idea.description[:400]}

Idea ID: {idea.id}
"""
        
        try:
            cmd = [
                "python3", str(task_manager),
                "add", title,
                "--priority", idea.task_priority,
                "--tags", ','.join(tags),
                "--desc", desc
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=task_manager.parent
            )
            
            if result.returncode == 0:
                # Parse task ID from output
                for line in result.stdout.split('\n'):
                    if 'ID:' in line or 'Created' in line:
                        parts = line.replace(':', ' ').split()
                        for part in parts:
                            if part.isdigit():
                                return part
            
        except Exception as e:
            print(f"Error creating task: {e}")
        
        return None
    
    def _is_agentmail_processed(self, message_id: str) -> bool:
        """Check if email was already processed."""
        processed_file = self.sources_dir / "agentmail" / "processed.jsonl"
        if not processed_file.exists():
            return False
        
        with open(processed_file) as f:
            for line in f:
                data = json.loads(line)
                if data.get('message_id') == message_id:
                    return True
        
        return False
    
    def _mark_agentmail_processed(self, message_id: str):
        """Mark email as processed."""
        processed_dir = self.sources_dir / "agentmail"
        processed_dir.mkdir(exist_ok=True)
        
        processed_file = processed_dir / "processed.jsonl"
        with open(processed_file, 'a') as f:
            f.write(json.dumps({
                'message_id': message_id,
                'processed_at': datetime.now().isoformat()
            }) + '\n')
    
    def _update_preferences(self, idea: Idea):
        """Update preference learning with outcome."""
        prefs_file = self.workspace / "preferences" / "user-profile.json"
        prefs_file.parent.mkdir(exist_ok=True)
        
        prefs = {}
        if prefs_file.exists():
            with open(prefs_file) as f:
                prefs = json.load(f)
        
        # Track types we pursue vs reject
        if idea.status == "pursued":
            prefs.setdefault('pursued_types', []).append(idea.source)
        elif idea.status == "rejected":
            prefs.setdefault('rejected_types', []).append(idea.source)
        
        # Track score accuracy
        if idea.actual_revenue and idea.revenue_monthly:
            estimate_accuracy = idea.actual_revenue / idea.revenue_monthly
            prefs.setdefault('revenue_accuracy', []).append(estimate_accuracy)
        
        # Track effort accuracy
        if idea.actual_hours:
            prefs.setdefault('effort_patterns', []).append({
                'estimated_effort': idea.effort_level,
                'actual_hours': idea.actual_hours
            })
        
        with open(prefs_file, 'w') as f:
            json.dump(prefs, f, indent=2)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Idea Tracker - Business Opportunity Pipeline")
    parser.add_argument('command', choices=['process', 'process-all', 'backlog', 'add'])
    parser.add_argument('--source', default='all', help='Source to process')
    parser.add_argument('--since-days', type=int, default=7, help='Days to look back')
    parser.add_argument('--top', type=int, default=10, help='Number of backlog items')
    parser.add_argument('--name', help='Idea name (for manual add)')
    parser.add_argument('--revenue', type=int, help='Monthly revenue (for manual add)')
    parser.add_argument('--startup-cost', default='Medium', help='Low/Medium/High')
    parser.add_argument('--effort', default='Medium', help='Low/Medium/High')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    
    args = parser.parse_args()
    
    tracker = IdeaTracker()
    
    if args.command in ['process', 'process-all']:
        source = 'all' if args.command == 'process-all' else args.source
        report = tracker.process_source(source, args.since_days, args.dry_run)
        print(report.summary())
    
    elif args.command == 'backlog':
        tracker.show_backlog(top_n=args.top)
    
    elif args.command == 'add':
        if not args.name or not args.revenue:
            print("Error: --name and --revenue required for manual add")
            return
        
        idea = tracker.add_idea(
            name=args.name,
            description=f"Manual entry",
            revenue_monthly=args.revenue,
            startup_cost=args.startup_cost,
            effort_level=args.effort
        )
        print(f"Added idea: {idea.name}")
        print(f"Task ID: {idea.task_id if idea.task_id else 'N/A (below threshold)'}")


if __name__ == "__main__":
    main()