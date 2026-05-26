#!/usr/bin/env python3
"""
Behavior Engine - Human-Like Interaction Simulation

Generates realistic mouse movements, scrolling, delays, and browsing patterns
to evade behavioral detection systems.
"""

import asyncio
import logging
import random
import math
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Point:
    """2D point for mouse coordinates."""
    x: float
    y: float
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
        
    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)


class BehaviorEngine:
    """
    Generates human-like browsing behavior.
    
    Features:
    - Bezier curve mouse movements with variable speed
    - Natural scrolling with breaks and focus areas
    - Randomized delays with realistic distributions
    - Micro-movements and idle behaviors
    
    Usage:
        engine = BehaviorEngine()
        await engine.human_delay(2)  # Wait 2s with variance
        await engine.smooth_scroll(page, distance=500)
    """
    
    def __init__(
        self,
        typing_speed_wpm: int = 50,  # Typing speed
        reading_speed_ms: int = 300,  # ms per word
        scroll_inertia: float = 0.8,  # How much momentum carries
    ):
        self.typing_speed_wpm = typing_speed_wpm
        self.reading_speed_ms = reading_speed_ms
        self.scroll_inertia = scroll_inertia
        
        # Current "attention" position (where human is looking)
        self.focus_point = Point(960, 540)  # Screen center
        
    async def human_delay(
        self,
        base_seconds: float,
        variance: float = 0.3,
        distribution: str = "gaussian",
    ):
        """
        Wait for human-like time with realistic variance.
        
        Args:
            base_seconds: Base delay time
            variance: Random variance factor (0-1)
            distribution: gaussian, uniform, or log_normal
        """
        if distribution == "gaussian":
            # Most realistic - occasional longer delays
            delay = random.gauss(base_seconds, base_seconds * variance)
        elif distribution == "log_normal":
            # Long-tail distribution (occasional much longer delays)
            delay = random.lognormvariate(
                math.log(base_seconds),
                variance
            )
        else:
            # Uniform
            delay = base_seconds + random.uniform(-variance, variance) * base_seconds
            
        delay = max(0.1, delay)  # Minimum 100ms
        await asyncio.sleep(delay)
        
    def generate_bezier_curve(
        self,
        start: Point,
        end: Point,
        control: Optional[Point] = None,
        steps: int = 30,
    ) -> List[Point]:
        """
        Generate a Bezier curve path from start to end.
        
        Creates organic, curved mouse movements instead of straight lines.
        """
        if control is None:
            # Generate control point for curve
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2
            
            # Add randomness to control point
            offset = random.randint(-100, 100)
            control = Point(mid_x + offset, mid_y - offset)
            
        points = []
        for t in [i / steps for i in range(steps + 1)]:
            # Quadratic Bezier formula
            p0 = start * ((1 - t) ** 2)
            p1 = control * (2 * (1 - t) * t)
            p2 = end * (t ** 2)
            point = p0 + p1 + p2
            points.append(point)
            
        return points
        
    def add_jitter(self, points: List[Point], jitter_amount: float = 2.0) -> List[Point]:
        """Add micro-jitter to simulate human hand tremor."""
        jittered = []
        for p in points:
            jitter_x = random.gauss(0, jitter_amount)
            jitter_y = random.gauss(0, jitter_amount)
            jittered.append(Point(p.x + jitter_x, p.y + jitter_y))
        return jittered
        
    async def move_mouse_realistic(
        self,
        page_or_tab,
        target_x: int,
        target_y: int,
        duration: float = 0.5,
    ):
        """
        Move mouse with realistic human-like behavior.
        
        Simulates:
        - Overshooting and correcting
        - Variable speed (fast start, slow approach)
        - Small circle at target (settling)
        """
        start = self.focus_point
        end = Point(target_x, target_y)
        
        # Generate curved path
        path = self.generate_bezier_curve(start, end)
        path = self.add_jitter(path)
        
        # Calculate variable speed (ease out)
        steps = len(path)
        for i, point in enumerate(path):
            # Ease-out curve: faster at start, slower near end
            progress = i / steps
            ease = 1 - (1 - progress) ** 3  # Cubic ease
            step_duration = (duration / steps) * (0.3 + 0.7 * (1 - ease))
            
            try:
                # Different APIs for nodriver vs playwright
                if hasattr(page_or_tab, 'mouse_move'):  # Playwright
                    await page_or_tab.mouse.move(int(point.x), int(point.y))
                elif hasattr(page_or_tab, 'evaluate'):  # Nodriver/generic
                    await page_or_tab.evaluate(
                        f"window.moveTo({int(point.x)}, {int(point.y)})"
                    )
            except:
                pass  # API might not support direct mouse movement
                
            await asyncio.sleep(step_duration)
            
        # Occasional "settling" at target
        if random.random() < 0.3:
            for _ in range(3):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                try:
                    if hasattr(page_or_tab, 'mouse_move'):
                        await page_or_tab.mouse.move(
                            int(target_x + offset_x),
                            int(target_y + offset_y)
                        )
                except:
                    pass
                await asyncio.sleep(0.05)
                
        # Update focus point
        self.focus_point = end
        
    async def scroll_natural(
        self,
        page_or_tab,
        target_scroll: int = 500,
        duration: float = 1.5,
    ):
        """
        Scroll with human-like behavior.
        
        - Variable speed (faster at start, slower near content)
        - Occasional pauses to "read"
        - Small overshoot and correction
        """
        current_scroll = 0
        start_time = time.time()
        
        while current_scroll < target_scroll:
            elapsed = time.time() - start_time
            if elapsed > duration:
                break
                
            # Variable step size based on position
            remaining = target_scroll - current_scroll
            base_step = min(50, remaining / 5 + 20)
            step = int(random.gauss(base_step, base_step * 0.2))
            step = max(10, min(step, remaining))
            
            # Scroll
            try:
                if hasattr(page_or_tab, 'evaluate'):  # Works for both
                    await page_or_tab.evaluate(f"window.scrollBy(0, {step})")
            except Exception as e:
                logger.warning(f"Scroll failed: {e}")
                break
                
            current_scroll += step
            
            # Random pauses (reading behavior)
            if random.random() < 0.15:
                await asyncio.sleep(random.uniform(0.5, 1.5))
            else:
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
        # Final "reading" pause
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
    async def browse_page_human(
        self,
        page_or_tab,
        scroll_depth: float = 0.7,  # How much of page to scroll (0-1)
    ):
        """
        Simulate complete browsing session.
        
        1. Initial reading pause
        2. Scroll through content with variable behavior
        3. Occasional "interest" pauses
        4. Return to top or continued browsing
        """
        # Initial examine
        await self.human_delay(random.uniform(1, 3))
        
        # Get page height
        try:
            page_height = await page_or_tab.evaluate(
                "document.body.scrollHeight"
            ) or 2000
            scroll_target = int(page_height * scroll_depth)
        except:
            scroll_target = 2000
            
        # Scroll behavior
        scrolled = 0
        section_size = random.randint(400, 800)
        
        while scrolled < scroll_target:
            section = min(section_size, scroll_target - scrolled)
            await self.scroll_natural(page_or_tab, section)
            scrolled += section
            
            # "Reading" pause
            if random.random() < 0.6:
                await self.human_delay(random.uniform(1, 3))
                
            # Random "interest" - examine an element
            if random.random() < 0.2:
                await self.examine_element(page_or_tab)
                
        # End behavior
        if random.random() < 0.5:
            # Return to top
            await page_or_tab.evaluate("window.scrollTo(0, 0)")
            await self.human_delay(0.5)
            
    async def examine_element(self, page_or_tab):
        """Simulate examining a specific element (hover, small movement)."""
        # Random position near center
        x = random.randint(400, 1000)
        y = random.randint(300, 700)
        
        await self.move_mouse_realistic(page_or_tab, x, y, duration=0.3)
        await self.human_delay(random.uniform(0.5, 1.5))
        
    def should_perform_action(self, probability: float) -> bool:
        """Decide whether to perform an optional action."""
        return random.random() < probability
        
    async def idle_behavior(self, page_or_tab, duration: float = 5.0):
        """Simulate idle time (switching tabs, distractions, etc.)."""
        start = time.time()
        
        while time.time() - start < duration:
            # Small random movements
            if random.random() < 0.3:
                offset = Point(random.randint(-20, 20), random.randint(-20, 20))
                new_pos = Point(
                    min(max(self.focus_point.x + offset.x, 0), 1920),
                    min(max(self.focus_point.y + offset.y, 0), 1080)
                )
                await self.move_mouse_realistic(
                    page_or_tab, int(new_pos.x), int(new_pos.y), duration=0.2
                )
                
            await asyncio.sleep(random.uniform(0.5, 2.0))


# Detection signature randomization
def randomize_viewport() -> dict:
    """Generate realistic viewport dimensions."""
    common_resolutions = [
        {"width": 1920, "height": 1080, "scale": 1.0},
        {"width": 1366, "height": 768, "scale": 1.0},
        {"width": 1440, "height": 900, "scale": 2.0},
        {"width": 1536, "height": 864, "scale": 1.25},
        {"width": 1280, "height": 720, "scale": 1.0},
    ]
    return random.choice(common_resolutions)
    
    
def generate_behavior_profile() -> dict:
    """Generate a complete behavior profile for a session."""
    return {
        "scroll_speed": random.gauss(1.0, 0.3),
        "mouse_speed": random.gauss(1.0, 0.2),
        "reading_time": random.gauss(300, 50),  # ms per word
        "attention_span": random.gauss(30, 10),  # seconds before distraction
        "click_precision": random.gauss(0.95, 0.05),  # accuracy
        "prefers_keyboard": random.random() < 0.2,  # 20% prefer keyboard nav
    }


if __name__ == "__main__":
    import sys
    
    async def test():
        engine = BehaviorEngine()
        
        print("Testing behavior patterns:")
        
        print("\n1. Human delay patterns:")
        for _ in range(3):
            start = time.time()
            await engine.human_delay(1.0)
            print(f"   Delay: {time.time() - start:.2f}s")
            
        print("\n2. Behavior profile:")
        profile = generate_behavior_profile()
        for key, val in profile.items():
            print(f"   {key}: {val:.2f}")
            
        print("\n3. Viewport options:")
        for _ in range(3):
            vp = randomize_viewport()
            print(f"   {vp['width']}x{vp['height']} @ {vp['scale']}x")
            
    asyncio.run(test())
