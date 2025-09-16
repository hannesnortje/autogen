#!/usr/bin/env python3
"""Demo script to showcase multi-framework component generation."""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.agents import CoderAgent


async def demo_multi_framework():
    """Demonstrate components for different frameworks."""
    agent = CoderAgent(name="MultiFrameworkDemo", role="Universal component generator")

    print("🚀 Multi-Framework Component Generation Demo")
    print("=" * 60)
    print()

    # Test React Hero Component
    print("🔵 REACT Hero Component")
    print("-" * 30)
    react_code = await agent.generate_component(
        objective="Create a React hero section with modern styling",
        component_name="ModernHero",
    )
    # Save React component
    with open("/tmp/ModernHero.jsx", "w") as f:
        f.write(react_code)
    print("✅ React hero component generated and saved to /tmp/ModernHero.jsx")
    print(f"📏 Code length: {len(react_code)} characters")
    print()

    # Test Lit 3 Web Component
    print("🟡 LIT 3 Web Component Card")
    print("-" * 30)
    lit_code = await agent.generate_component(
        objective="Create a Lit web component card for displaying content",
        component_name="ContentCard",
    )
    # Save Lit component
    with open("/tmp/ContentCard.js", "w") as f:
        f.write(lit_code)
    print("✅ Lit 3 card component generated and saved to /tmp/ContentCard.js")
    print(f"📏 Code length: {len(lit_code)} characters")
    print()

    # Test C++ RAII Class
    print("🔴 C++ RAII Resource Management")
    print("-" * 30)
    cpp_code = await agent.generate_component(
        objective="Create a C++ RAII class for safe resource handling",
        component_name="SafeResource",
    )
    # Save C++ class
    with open("/tmp/SafeResource.hpp", "w") as f:
        f.write(cpp_code)
    print("✅ C++ RAII class generated and saved to /tmp/SafeResource.hpp")
    print(f"📏 Code length: {len(cpp_code)} characters")
    print()

    # Test Vue Component (fallback)
    print("🟢 VUE Component (Default)")
    print("-" * 30)
    vue_code = await agent.generate_component(
        objective="Create an interactive Vue component for user dashboard",
        component_name="UserDashboard",
    )
    # Save Vue component
    with open("/tmp/UserDashboard.vue", "w") as f:
        f.write(vue_code)
    print("✅ Vue dashboard component generated and saved to /tmp/UserDashboard.vue")
    print(f"📏 Code length: {len(vue_code)} characters")
    print()

    print("🎉 Multi-Framework Demo Complete!")
    print("Files generated in /tmp/ directory:")
    print("  - ModernHero.jsx (React)")
    print("  - ContentCard.js (Lit 3)")
    print("  - SafeResource.hpp (C++)")
    print("  - UserDashboard.vue (Vue)")


if __name__ == "__main__":
    asyncio.run(demo_multi_framework())
