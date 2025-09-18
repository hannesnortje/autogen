# Technical Documentation: Memory System

## Memory Scopes in AutoGen

AutoGen implements a sophisticated multi-scope memory architecture that allows agents to access different types of knowledge based on context.

### Available Memory Scopes

1. **Global Scope** (`global`)
   - Universal knowledge and best practices
   - Coding standards and design patterns
   - Security guidelines and architectural principles
   - Shared across all projects and agents

2. **Project Scope** (`project`)
   - Project-specific context and requirements
   - API documentation and architecture decisions
   - Known issues and project-specific solutions
   - Team conventions and project standards

3. **Agent Scope** (`agent`)
   - Agent-specific knowledge and capabilities
   - Specialized domain expertise
   - Personal agent history and learned patterns
   - Agent-specific configurations and preferences

4. **Thread Scope** (`thread`)
   - Conversation context and recent interactions
   - Current task context and decisions made
   - Ongoing problem-solving state
   - Short-term working memory

5. **Objectives Scope** (`objectives`)
   - Current goals and milestones
   - Sprint objectives and OKRs
   - Task priorities and deadlines
   - Success criteria and metrics

6. **Artifacts Scope** (`artifacts`)
   - Build results and deployment history
   - Generated code and documentation
   - Test results and performance metrics
   - Release notes and changelog data

## Memory Operations

### Upload Process
1. File selection and validation
2. Content chunking and preprocessing
3. Embedding generation using sentence transformers
4. Vector storage in Qdrant collections
5. Metadata indexing for retrieval

### Search and Retrieval
- Semantic similarity search using dense vectors
- Hybrid search combining multiple retrieval methods
- Scope-specific filtering and ranking
- Relevance scoring and result limitation

### Statistics and Monitoring
- Document count per collection
- Vector space utilization metrics
- Search performance analytics
- Collection health monitoring
