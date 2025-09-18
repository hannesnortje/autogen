# Development Testing Scripts

This directory contains development and debugging scripts used during the AutoGen project development process. These files are preserved for historical reference and potential future debugging needs.

## File Categories

### Integration Tests
- `test_agent_persistence.py` - Agent lifecycle testing (create, save, load, delete)
- `test_conversation_integration.py` - Conversation service integration testing
- `test_deletion_integration.py` - Memory deletion functionality testing
- `test_ui_integration.py` - UI component integration testing
- `test_step6_2_export_import.py` - Data export/import testing

### Memory System Tests
- `test_memory_search.py` - Memory search functionality testing
- `test_seeding_final.py` - Memory knowledge seeding tests
- `test_seeding_fix.py` - Seeding deduplication fix tests
- `test_collection_fix.py` - Collection management fix tests
- `test_search_debug.py` - Search debugging tests

### Development Artifacts
- `phase3_results.json` - Test results from Phase 3 validation
- `AutogenSpecs_Expanded.md` - Expanded system specifications from early development
- `MyComponent.vue` - Vue 3 component example from UI development
- `server.log`, `server_output.log`, `server_test.log`, `server_ui_test.log` - Server runtime logs

## Usage Notes

These scripts were used during development to:
1. Test specific functionality in isolation
2. Debug integration issues
3. Validate fixes and improvements
4. Perform end-to-end testing

For current testing, use the formal test suite in the `tests/` directory:
```bash
poetry run pytest tests/
```

## Historical Context

These files represent the iterative development and testing process that led to the production-ready AutoGen system. They demonstrate the thorough validation approach used during development phases.
