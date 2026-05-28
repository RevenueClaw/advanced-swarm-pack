#!/usr/bin/env python3
"""
skill-premortem-v1: Structured failure analysis for countering optimism bias.

Main exports:
- PremortemAnalyzer: Core analysis engine
- PremortemIntegrations: Connectors for Architect-First, Estimation, Consensus

Quick Start:
    from skill_premortem_v1.lib import PremortemAnalyzer
    
    analyzer = PremortemAnalyzer()
    result = analyzer.premortem(
        goal="Launch price tracking feature",
        proposed_plan=["Build API integration", "Add notifications", "Deploy"],
        context="Production e-commerce system",
        risk_tolerance="medium",
        depth="standard"
    )
"""

from .premortem_analyzer import (
    PremortemAnalyzer,
    RiskTolerance,
    DepthLevel,
    FailureMode,
    TailRisk,
    HiddenAssumption,
    EarlyWarningIndicator,
    Mitigation,
    RevisedStep,
    PremortemResult
)

from .integrations import PremortemIntegrations

__all__ = [
    # Core analyzer
    "PremortemAnalyzer",
    
    # Integration helper
    "PremortemIntegrations",
    
    # Enums and dataclasses
    "RiskTolerance",
    "DepthLevel",
    "FailureMode", 
    "TailRisk",
    "HiddenAssumption",
    "EarlyWarningIndicator",
    "Mitigation",
    "RevisedStep",
    "PremortemResult"
]

__version__ = "1.0.0"
__author__ = "RockClaw"
