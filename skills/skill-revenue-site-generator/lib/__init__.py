#!/usr/bin/env python3
"""
skill-revenue-site-generator: Production-safe revenue site generation.

Main exports:
- RevenueSiteGenerator: Create conversion-optimized affiliate sites
- SafeDeployer: Deploy with automatic rollback on failure
- ProductData: Product with pricing info
- RevenueSite: Complete deployable site

Quick Start:
    from skill_revenue_site_generator.lib import RevenueSiteGenerator, SafeDeployer
    
    # Generate site
    gen = RevenueSiteGenerator()
    site = gen.generate_comparison_site(
        niche="sbc-deals",
        products=[p1, p2, p3],
        affiliate_tag="vhicklegar011-20"
    )
    
    # Deploy safely
    deployer = SafeDeployer("/var/www/revenue-sites")
    result = deployer.deploy_with_rollback(site, "deals.chipradar.com")
    
    if not result.success:
        print(f"Deploy failed: {result.revenue_impact}")
        deployer.manual_rollback("deals.chipradar.com", result.deployment_id)
"""

from .site_generator import (
    RevenueSiteGenerator,
    ProductData,
    RevenueSite,
    generate_chipradar_deals_site
)

from .safe_deployer import SafeDeployer, DeploymentResult

__all__ = [
    "RevenueSiteGenerator",
    "SafeDeployer",
    "ProductData",
    "RevenueSite",
    "DeploymentResult",
    "generate_chipradar_deals_site"
]

__version__ = "1.0.0"
__author__ = "RockClaw"
