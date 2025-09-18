# API Reference Guide

## AutoGen MCP Server Endpoints

### Memory Management Endpoints

#### POST /memory/upload
Upload and process files into memory collections.

**Parameters:**
- `file`: Multipart file upload
- `project`: Project identifier (default: "default")
- `scope`: Memory scope (project, global, agent, thread, objectives, artifacts)

**Response:**
```json
{
  "success": true,
  "chunks_processed": 15,
  "message": "File uploaded successfully"
}
```

#### GET /memory/search
Search memory collections for relevant information.

**Parameters:**
- `query`: Search query string
- `collection`: Target collection name (optional)
- `limit`: Maximum results to return (default: 10)
- `scope`: Memory scope filter (optional)

**Response:**
```json
{
  "results": [
    {
      "content": "Relevant text content...",
      "metadata": {
        "source": "filename.md",
        "chunk_id": "chunk_1",
        "scope": "project"
      },
      "score": 0.85
    }
  ]
}
```

#### GET /memory/stats
Get memory collection statistics.

**Response:**
```json
{
  "autogen_project": {
    "documents_count": 42,
    "vectors_count": 42,
    "status": "green"
  },
  "summary": {
    "total_documents": 42,
    "collections_ready": 3,
    "overall_status": "ready"
  }
}
```

#### DELETE /memory/collections/{collection_name}
Delete a memory collection and all its data.

**Parameters:**
- `collection_name`: Name of collection to delete

**Response:**
```json
{
  "success": true,
  "message": "Collection deleted successfully"
}
```

### Agent Management Endpoints

#### GET /agents/available
Get list of available agents including custom agents.

#### POST /agents/custom
Create or update custom agent configuration.

#### DELETE /agents/custom/{agent_name}
Delete a custom agent configuration.
