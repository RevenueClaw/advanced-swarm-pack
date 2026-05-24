# Newsletter Processor

Extract business ideas from email newsletters and integrate with income generation workflow.

## Overview

Monitors AgentMail inbox for newsletters (Side Hustle Nation, etc.), extracts business opportunities, and feeds them into the income generation audit system.

## Features

- **Automatic Processing**: Scans inbox weekly for new newsletters
- **Smart Extraction**: Pulls revenue numbers, startup costs, business types
- **Relevance Scoring**: HIGH/MEDIUM/LOW relevance to AI/agents
- **Storage**: JSONL for audit trail, JSON for summaries
- **Integration**: Ties into existing income-automation-audit cron job

## Quick Start

```python
from lib.newsletter_processor import run_newsletter_processing

# Run manually
run_newsletter_processing()

# Or import and use
from lib.newsletter_processor import NewsletterProcessor

processor = NewsletterProcessor()
ideas = processor.process_newsletters(since_days=7)
high_ideas = processor.get_high_relevance_ideas()
```

## Storage

- **Ideas Log**: `~/.openclaw/workspace/newsletter-ideas/extracted-ideas.jsonl`
- **Summary**: `~/.openclaw/workspace/newsletter-ideas/ideas-summary.json`

## Cron Integration

Add to existing income-automation-audit job or create separate weekly job:

```bash
# ~/.openclaw/cron/newsletter-processor.sh
source ~/.openclaw/credentials/agentmail.env
cd ~/.openclaw/workspace/skills/skill-newsletter-processor
python3 lib/newsletter_processor.py >> ~/.openclaw/logs/newsletter.log 2>&1
```

## Supported Sources

- Side Hustle Nation (nick@sidehustlenation.com)
- Easy to add more sources in NEWSLETTER_SOURCES config

## Relevance Scoring

| Level | Criteria | Action |
|-------|----------|--------|
| HIGH | AI/automation/software focus | Flag for immediate review |
| MEDIUM | Digital/service businesses | Include in monthly audit |
| LOW | Physical products/hard goods | Archive, low priority |

## Output Format

Each extracted idea includes:
- Business name/type
- Revenue potential
- Startup cost estimate
- Relevance score
- Source newsletter
- Extraction date
