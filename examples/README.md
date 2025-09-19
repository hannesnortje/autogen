# AutoGen Examples

This directory contains demonstration scripts showing how to use various AutoGen features.

## Available Examples

### `scrum_lit3_builder.py`
Demonstrates the scrum agent collaboration system:
- Multi-agent scrum planning sessions
- User story generation and prioritization
- Technical decision making with agents
- Lit 3 project generation from scrum output
- Complete end-to-end development workflow

**Usage**: Shows how AutoGen agents can collaborate using scrum methodology to plan and build a complete web application project.

### `demo_cross_project_learning.py`
Demonstrates the cross-project learning capabilities:
- Project registration and similarity matching
- Solution reuse and adaptation
- Best practice propagation
- Global knowledge integration

**Usage**: Shows how to use the CrossProjectLearningService to analyze patterns across multiple projects and generate intelligent recommendations.

### `demo_frameworks.py`
Demonstrates multi-framework integration patterns:
- Framework-specific agent configurations
- Integration with different development stacks
- Workflow orchestration examples

**Usage**: Provides examples of how AutoGen can work with various development frameworks and toolchains.

## Running Examples

All examples can be run using Poetry from the project root:

```bash
# From /media/hannesn/storage/Code/autogen/
poetry run python examples/scrum_lit3_builder.py
poetry run python examples/demo_cross_project_learning.py
poetry run python examples/demo_frameworks.py
```

## Prerequisites

- AutoGen MCP server running (see main README.md)
- Qdrant vector database accessible
- Required API keys configured in `.env` file

## Contributing

When adding new examples:
1. Follow the naming pattern: `demo_<feature_name>.py`
2. Include comprehensive docstrings
3. Add entry to this README
4. Ensure examples work with current MCP server version
