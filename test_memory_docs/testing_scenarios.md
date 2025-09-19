# Testing Scenarios for Memory Upload

## Test Case 1: Basic Upload Functionality
**Objective**: Verify that markdown files can be uploaded successfully to memory.

**Steps**:
1. Start AutoGen system
2. Navigate to Memory > Upload Files
3. Upload `project_overview.md` with scope "project"
4. Check for success message
5. Verify statistics show increased document count

**Expected Results**:
- Upload completes without errors
- Document count increases in project collection
- File appears in memory search results

## Test Case 2: Multiple Scope Testing
**Objective**: Test uploading documents to different memory scopes.

**Steps**:
1. Upload `technical_docs.md` with scope "global"
2. Upload `api_reference.md` with scope "project"
3. Upload `user_guide.md` with scope "thread"
4. Check statistics for each collection

**Expected Results**:
- Each scope gets its own collection
- Statistics show documents distributed across scopes
- Search results can be filtered by collection

## Test Case 3: Search and Retrieval
**Objective**: Verify that uploaded content can be found through search.

**Test Queries**:
- "How do I upload files to memory?"
- "What are the available memory scopes?"
- "API endpoints for memory management"
- "AutoGen project structure"

**Expected Results**:
- Relevant results returned for each query
- Results ranked by relevance score
- Content matches uploaded documents

## Test Case 4: Statistics Monitoring
**Objective**: Verify that memory statistics update correctly.

**Metrics to Check**:
- Total document count across all collections
- Documents per collection/scope
- Collection health status
- Vector count matches document count

**Expected Results**:
- Statistics reflect actual uploaded content
- All collections show "green" healthy status
- Refresh updates numbers correctly

## Test Case 5: Collection Management
**Objective**: Test collection listing and potential cleanup.

**Steps**:
1. View Collections tab to see all created collections
2. Note collection names and document counts
3. Identify collections for potential deletion
4. Test search before and after collection changes

**Expected Results**:
- Collections tab shows accurate information
- Collection names follow expected pattern
- Search results change when collections are modified

## Performance Testing Notes

**Document Size Limits**:
- Test with small files (< 1KB)
- Test with medium files (1-10KB)
- Test with large files (> 50KB)

**Content Types**:
- Simple text documents
- Documents with code blocks
- Documents with tables and lists
- Documents with special characters

**Upload Volume**:
- Single file uploads
- Multiple sequential uploads
- Batch upload scenarios (if supported)

## Cleanup and Reset

After testing, you may want to:
1. Note which collections were created
2. Document any issues or unexpected behavior
3. Consider clearing test data before production use
4. Reset collections if needed for clean state

## Troubleshooting Common Issues

**Upload Failures**:
- Check file format (must be .md)
- Verify file size limits
- Check server logs for errors

**Search Issues**:
- Verify documents were uploaded successfully
- Check collection selection in search
- Try different query phrasings

**Statistics Problems**:
- Click Refresh Statistics button
- Check for server connection issues
- Verify collections exist in database
