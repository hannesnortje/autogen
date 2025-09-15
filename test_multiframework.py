#!/usr/bin/env python3
"""Test script to verify multi-framework component generation works."""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.agents import CoderAgent


async def test_frameworks():
    """Test generating components for different frameworks."""
    agent = CoderAgent(
        name="TestCoder",
        role="Component generator for testing multi-framework patterns",
    )

    # Test React Hero Component
    print("=== Testing React Hero Component ===")
    react_result = await agent.generate_component(
        objective="Create a React hero section component with call-to-action buttons",
        component_name="HeroSection",
    )
    print("React Hero Component:")
    print(react_result[:200] + "..." if len(react_result) > 200 else react_result)
    print()

    # Test Lit 3 Card Component
    print("=== Testing Lit 3 Card Component ===")
    lit_result = await agent.generate_component(
        objective="Create a Lit 3 web component card with image and content",
        component_name="CardComponent",
    )
    print("Lit 3 Card Component:")
    print(lit_result[:200] + "..." if len(lit_result) > 200 else lit_result)
    print()

    # Test C++ RAII Class
    print("=== Testing C++ RAII Class ===")
    cpp_result = await agent.generate_component(
        objective="Create a C++ RAII class for resource management",
        component_name="ResourceManager",
    )
    print("C++ RAII Class:")
    print(cpp_result[:200] + "..." if len(cpp_result) > 200 else cpp_result)
    print()

    # Test Vue Component (original)
    print("=== Testing Vue Hero Component ===")
    vue_result = await agent.generate_component(
        objective="Create a Vue hero section with dynamic content",
        component_name="VueHero",
    )
    print("Vue Hero Component:")
    print(vue_result[:200] + "..." if len(vue_result) > 200 else vue_result)
    print()


if __name__ == "__main__":
    asyncio.run(test_frameworks())
