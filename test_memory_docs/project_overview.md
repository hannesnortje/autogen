# AutoGen Project Overview

## Introduction
AutoGen is a multi-agent conversation framework that enables the creation of sophisticated AI systems. This project implements memory persistence and multi-scope agent capabilities.

## Key Features

### Agent Management
- Persistent agent storage in JSON configuration
- Multiple memory scope selection (global, project, agent, thread, objectives, artifacts)
- Agent duplication and customization capabilities
- UI-driven agent creation and management

### Memory Architecture
- Qdrant vector database for semantic memory storage
- Multi-scope memory isolation and retrieval
- Hybrid search combining dense and sparse retrieval
- File upload and chunking for knowledge base creation

### Technical Stack
- **Backend**: FastAPI with AutoGen MCP server
- **Database**: Qdrant vector database
- **UI**: PySide6 (Qt6) desktop application
- **Memory**: Embedding-based semantic search
- **Languages**: Python with Poetry dependency management

## Project Structure
```
src/
├── autogen_mcp/     # MCP server and memory services
├── autogen_ui/      # Desktop UI components
└── tests/           # Comprehensive test suites
```

## Development Status
- ✅ Core memory persistence implemented
- ✅ Multi-scope agent system working
- ✅ Desktop UI with file upload capabilities
- ✅ Statistics and monitoring features
- 🔄 Currently testing memory upload functionality
