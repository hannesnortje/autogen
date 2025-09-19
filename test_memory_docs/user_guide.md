# User Guide: Getting Started with AutoGen Memory

## Overview
This guide will walk you through using AutoGen's memory system to upload documents, search for information, and manage your knowledge base.

## Step 1: Starting AutoGen

1. Open a terminal in your AutoGen project directory
2. Run the launcher: `poetry run python launch.py`
3. Wait for all components to start (Qdrant, MCP server, UI)
4. The AutoGen Desktop UI should open automatically

## Step 2: Uploading Documents

### Using the Desktop UI
1. Click on the **Memory** tab
2. Go to the **Upload Files** sub-tab
3. Click **Browse Files...** to select a markdown file
4. Choose your target **Project** (or use "default")
5. Select appropriate **Scope** (project, global, etc.)
6. Click **Upload to Memory**

### What Happens During Upload
- File is read and validated
- Content is split into semantic chunks
- Each chunk is converted to embeddings
- Vectors are stored in Qdrant database
- Metadata is preserved for later retrieval

## Step 3: Searching Memory

### Basic Search
1. Go to the **Search Results** tab in Memory
2. Enter your search query in the text field
3. Optionally select a specific collection
4. Set the limit for number of results
5. Click **Search**

### Understanding Results
- Results are ranked by semantic similarity
- Each result shows content snippet and metadata
- Score indicates relevance (higher = more relevant)
- Click on results to see full content

## Step 4: Monitoring Statistics

### Viewing Stats
1. Click the **Statistics** tab
2. Click **Refresh Statistics** to update
3. View document counts per collection
4. Check collection health status

### What Statistics Show
- **Documents Count**: Number of text chunks stored
- **Vectors Count**: Number of embedding vectors
- **Status**: Collection health (green = healthy)
- **Collections Ready**: How many collections are active

## Step 5: Managing Collections

### Viewing Collections
- Use the **Collections** tab to see all collections
- Each collection corresponds to a memory scope
- Collections are created automatically when uploading

### Deleting Memory Data
- Currently done via API or direct database access
- Future UI versions will include delete functionality
- Be careful - deletion is permanent!

## Tips and Best Practices

1. **Choose Appropriate Scopes**:
   - Use `project` for project-specific documentation
   - Use `global` for universal knowledge and standards
   - Use `thread` for conversation-specific context

2. **Optimize Your Documents**:
   - Use clear headings and structure
   - Include relevant keywords
   - Keep chunks focused and coherent

3. **Search Effectively**:
   - Use specific, descriptive queries
   - Try different phrasings if results aren't relevant
   - Use collection filters to narrow results

4. **Monitor Performance**:
   - Check statistics regularly
   - Watch for collection health issues
   - Clean up unused collections periodically
