#!/usr/bin/env python3
"""
Morning Digest Generator - Create human-readable batch reports.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class DigestEntry:
    """Single job entry in digest."""
    job_name: str
    status: str
    tokens_generated: int
    confidence: float
    output_summary: str = ""
    error: Optional[str] = None


class MorningDigestGenerator:
    """Generate morning batch digests."""
    
    def __init__(self, digests_dir: Path):
        self.digests_dir = digests_dir
        self.digests_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_text_digest(
        self,
        date: str,
        jobs_completed: int,
        cloud_tokens_avoided: int,
        escalated_count: int,
        failed_count: int,
        avg_confidence: float,
        entries: List[DigestEntry]
    ) -> str:
        """Generate plain text digest."""
        lines = [
            f"=== Overnight Local Swarm Report ===",
            f"Date: {date}",
            "",
            f"Jobs completed: {jobs_completed}",
            f"Cloud tokens avoided: ~{cloud_tokens_avoided:,}",
            f"Escalated to cloud: {escalated_count}",
            f"Failed: {failed_count}",
            f"Average local confidence: {avg_confidence:.2f}", 
            "",
            "=== Top Outputs ===",
        ]
        
        for entry in entries:
            lines.append(f"\n[{entry.job_name}]")
            lines.append(f"  Status: {entry.status}")
            lines.append(f"  Confidence: {entry.confidence:.2f}")
            if entry.output_summary:
                lines.append(f"  Summary: {entry.output_summary}")
            if entry.error:
                lines.append(f"  Error: {entry.error}")
        
        return "\n".join(lines)
    
    def save_digest(self, date: str, digest_text: str) -> Path:
        """Save digest to file."""
        digest_path = self.digests_dir / f"digest_{date}.txt"
        with open(digest_path, 'w') as f:
            f.write(digest_text)
        return digest_path


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        gen = MorningDigestGenerator(Path(d) / "digests")
        
        entry = DigestEntry(
            "newsletter_digest",
            "completed",
            5000,
            0.85,
            "6 newsletter ideas processed"
        )
        
        digest = gen.generate_text_digest(
            date="2026-05-30",
            jobs_completed=14,
            cloud_tokens_avoided=88000,
            escalated_count=2,
            failed_count=1,
            avg_confidence=0.78,
            entries=[entry]
        )
        
        print(digest)
