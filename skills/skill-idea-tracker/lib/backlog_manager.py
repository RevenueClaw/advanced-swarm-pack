#!/usr/bin/env python3
"""
Backlog Manager - Persistence and retrieval for ideas.

v1.0.1 - Production Release
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Dict

try:
    from .idea_tracker import Idea
except ImportError:
    from idea_tracker import Idea


class BacklogManager:
    """
    Manages idea persistence and retrieval.
    
    Storage format: JSONL (one JSON object per line)
    - Append-optimized
    - Line-safe (corruption affects only one record)
    - Easy to query with grep/jq
    """
    
    def __init__(self, backlog_dir: Path):
        self.backlog_dir = backlog_dir
        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        
        self.ideas_file = backlog_dir / "ideas.jsonl"
        self.id_index = {}  # In-memory cache
        self._load_index()
    
    def _load_index(self):
        """Build in-memory index of idea IDs."""
        self.id_index = {}
        if not self.ideas_file.exists():
            return
        
        with open(self.ideas_file) as f:
            for line_num, line in enumerate(f):
                try:
                    data = json.loads(line)
                    self.id_index[data['id']] = line_num
                except:
                    pass
    
    def add_idea(self, idea: Idea) -> bool:
        """
        Add idea to backlog.
        
        Returns:
            True if added, False if already exists
        """
        if idea.id in self.id_index:
            return False
        
        with open(self.ideas_file, 'a') as f:
            f.write(json.dumps(idea.to_dict()) + '\n')
        
        self.id_index[idea.id] = len(self.id_index)
        return True
    
    def is_tracked(self, idea_id: str) -> bool:
        """Check if idea is already tracked."""
        return idea_id in self.id_index
    
    def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Retrieve idea by ID."""
        if idea_id not in self.id_index:
            return None
        
        if not self.ideas_file.exists():
            return None
        
        with open(self.ideas_file) as f:
            for line in f:
                data = json.loads(line)
                if data['id'] == idea_id:
                    return Idea.from_dict(data)
        
        return None
    
    def get_all_ideas(self) -> List[Idea]:
        """Get all tracked ideas."""
        ideas = []
        
        if not self.ideas_file.exists():
            return ideas
        
        with open(self.ideas_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    ideas.append(Idea.from_dict(data))
                except:
                    pass
        
        return ideas
    
    def update_idea(self, idea: Idea) -> bool:
        """
        Update existing idea.
        
        Note: Since we use append-only format, we rewrite the file.
        For production with large backlogs, use a proper database.
        """
        if idea.id not in self.id_index:
            return False
        
        ideas = self.get_all_ideas()
        
        # Replace
        for i, existing in enumerate(ideas):
            if existing.id == idea.id:
                ideas[i] = idea
                break
        
        # Rewrite
        with open(self.ideas_file, 'w') as f:
            for i in ideas:
                f.write(json.dumps(i.to_dict()) + '\n')
        
        self._load_index()
        return True
    
    def get_stats(self) -> Dict:
        """Get backlog statistics."""
        ideas = self.get_all_ideas()
        
        return {
            'total_ideas': len(ideas),
            'new': sum(1 for i in ideas if i.status == 'new'),
            'scored': sum(1 for i in ideas if i.status == 'scored'),
            'tasked': sum(1 for i in ideas if i.status == 'tasked'),
            'pursued': sum(1 for i in ideas if i.status == 'pursued'),
            'rejected': sum(1 for i in ideas if i.status == 'rejected'),
            'high_value_count': sum(
                1 for i in ideas 
                if i.score and i.score.total_score >= 70
            )
        }
