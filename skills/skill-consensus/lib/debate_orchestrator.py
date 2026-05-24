#!/usr/bin/env python3
"""DebateOrchestrator - Lightweight multi-agent debate system.

Flow:
1. User submits uncertain/high-stakes question
2. Each persona presents initial position
3. Each critiques others' positions  
4. Pragmatic synthesizes final recommendation
5. Decision logged with reasoning

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

from agent_personas import AgentPersonas, AgentPersona


@dataclass
class DebatePosition:
    """A single agent's position."""
    agent: str
    position: str
    reasoning: str
    confidence: float  # 0.0-1.0
    flagged_risks: List[str]


@dataclass
class DebateTurn:
    """One round of debate."""
    round_num: int
    agent_responses: Dict[str, str]
    critiques: Dict[str, str]  # agent -> their critique of others


@dataclass
class DebateResult:
    """Final result of a debate."""
    debate_id: str
    timestamp: str
    question: str
    context: Dict[str, Any]
    positions: List[DebatePosition]
    synthesis: str
    recommendation: str
    caveats: List[str]
    confidence: float


def log_debate(result: DebateResult, log_dir: Path):
    """Archive debate for future reference."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m')}.jsonl"
    
    with open(log_file, "a") as f:
        f.write(json.dumps(asdict(result), default=str) + "\n")


class DebateOrchestrator:
    """
    Orchestrates multi-agent debate for uncertain decisions.
    
    Usage:
        orchestrator = DebateOrchestrator()
        result = orchestrator.debate(
            question="Should we migrate to new DB?",
            context={"current_db": "PostgreSQL", "proposal": "ClickHouse"},
            personas=AgentPersonas.get_three_persona_panel()
        )
    """
    
    RISK_THRESHOLD_FOR_DEBATE = 0.6
    MIN_CONFIDENCE_FOR_SOLO = 0.7
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(
            "/home/rock/.openclaw/workspace/skills/skill-consensus/debate_logs"
        )
    
    def should_debate(
        self,
        risk_score: float,
        confidence: float,
        has_rejection_history: bool,
        is_novel: bool
    ) -> bool:
        """
        Determine if a decision warrants debate.
        
        Args:
            risk_score: 0.0-1.0 (destructive, external action, etc.)
            confidence: 0.0-1.0 (learned pattern match certainty)
            has_rejection_history: User rejected similar before
            is_novel: No prior experience with this situation
        """
        # Always debate high-risk situations
        if risk_score >= self.RISK_THRESHOLD_FOR_DEBATE:
            return True
        
        # Debate if uncertain
        if confidence < self.MIN_CONFIDENCE_FOR_SOLO:
            return True
        
        # Debate if user has rejected similar
        if has_rejection_history:
            return True
        
        # Debate novel situations
        if is_novel:
            return True
        
        return False
    
    def debate(
        self,
        question: str,
        context: Dict[str, Any],
        personas: Optional[List[AgentPersona]] = None
    ) -> DebateResult:
        """
        Conduct multi-agent debate.
        
        In real implementation, this would spawn subagents.
        For now, returns structured framework for manual execution.
        """
        personas = personas or AgentPersonas.get_three_persona_panel()
        debate_id = hashlib.sha256(
            f"{question}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Build debate structure
        positions = []
        for persona in personas:
            positions.append(DebatePosition(
                agent=persona.name,
                position=f"[{persona.name} would formulate position here]",
                reasoning=f"Based on priority: {persona.priority}",
                confidence=0.0,
                flagged_risks=[]
            ))
        
        result = DebateResult(
            debate_id=debate_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            context=context,
            positions=positions,
            synthesis="[Pragmatic would synthesize here]",
            recommendation="[Final recommendation]",
            caveats=["[Risk flags from Conservative]"],
            confidence=0.0
        )
        
        # Log debate structure
        log_debate(result, self.log_dir)
        
        return result
    
    def get_debate_prompts(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate prompts for each debate participant.
        Returns prompts keyed by persona name.
        """
        personas = AgentPersonas.get_three_persona_panel()
        prompts = {}
        
        for persona in personas:
            prompts[persona.name] = f"""{persona.system_prompt_addendum}

DEBATE QUESTION: {question}
CONTEXT: {json.dumps(context, indent=2)}

Your task:
1. State your position clearly (2-3 sentences)
2. Provide your reasoning based on your priorities
3. Identify 2-3 specific risks or opportunities
4. Rate your confidence in this position (0.0-1.0)

Format:
Position: [your stance]
Reasoning: [why]
Risks/Opportunities: [list]
Confidence: [score]
"""
        
        return prompts


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("DEBATE ORCHESTRATOR - VERIFICATION TEST")
    print("=" * 60)
    
    # Initialize
    test_dir = Path(tempfile.mkdtemp())
    print(f"\n[1] Test environment: {test_dir}")
    
    orch = DebateOrchestrator(log_dir=test_dir)
    
    # Test should_debate logic
    print("\n[2] Testing debate trigger logic...")
    
    # High risk = debate
    assert orch.should_debate(risk_score=0.8, confidence=0.9, 
                               has_rejection_history=False, is_novel=False) == True
    print("    - High risk triggers debate ✓")
    
    # Low confidence = debate
    assert orch.should_debate(risk_score=0.2, confidence=0.5,
                               has_rejection_history=False, is_novel=False) == True
    print("    - Low confidence triggers debate ✓")
    
    # Novel situation = debate
    assert orch.should_debate(risk_score=0.2, confidence=0.8,
                               has_rejection_history=False, is_novel=True) == True
    print("    - Novel situation triggers debate ✓")
    
    # Safe + confident + familiar = no debate
    assert orch.should_debate(risk_score=0.2, confidence=0.8,
                               has_rejection_history=False, is_novel=False) == False
    print("    - Safe routine = no debate ✓")
    
    # Test prompt generation
    print("\n[3] Testing prompt generation...")
    prompts = orch.get_debate_prompts(
        question="Should we delete old logs?",
        context={"disk_usage": "85%", "log_age": "90 days"}
    )
    
    assert "Conservative" in prompts
    assert "Pragmatic" in prompts
    assert "Innovative" in prompts
    print(f"    - Generated {len(prompts)} persona prompts ✓")
    print(f"    - Conservative prompt length: {len(prompts['Conservative'])} chars ✓")
    
    # Test debate result structure
    print("\n[4] Testing debate result logging...")
    result = orch.debate(
        question="Should we migrate databases?",
        context={"current": "Postgres", "target": "ClickHouse"}
    )
    
    assert result.debate_id
    assert len(result.positions) == 3
    print(f"    - Debate ID: {result.debate_id} ✓")
    print(f"    - Positions: {len(result.positions)} ✓")
    
    # Test log file
    log_files = list(test_dir.glob("*.jsonl"))
    assert len(log_files) == 1
    print(f"    - Log file created: {log_files[0].name} ✓")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
