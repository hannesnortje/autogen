# 🧪 AutoGen UI Testing Guide

**Date**: September 16, 2025
**Branch**: `ui-step-1.3-memory-integration`
**Status**: Testing Step 1.3 Memory Integration

---

## 🚀 Quick Start - Complete System Test

### **Method 1: Full Integration Test (Recommended)**

This method tests both the MCP server and UI together for the complete experience:

#### **Step 1: Start MCP Server**
```bash
cd /media/hannesn/storage/Code/autogen

# Start the MCP server on port 9000
poetry run python -m autogen_mcp.mcp_server
```

The server should show:
```
INFO:     Uvicorn running on http://127.0.0.1:9000 (Press CTRL+C to quit)
```

#### **Step 2: Start UI (New Terminal)**
```bash
cd /media/hannesn/storage/Code/autogen

# Start the desktop UI
poetry run python -m src.autogen_ui.main
```

#### **Step 3: Test Memory Integration**
1. **Memory Tab**: Click the "Memory" tab in the left panel
2. **Connection Status**: Should show "Memory: Connected" (green)
3. **Search Test**:
   - Enter query like "test" or "hello"
   - Select scope (conversation/project/global)
   - Click "Search"
4. **Statistics**: Check memory stats in bottom panel
5. **Menu Test**: Use "Memory → Browser" menu item

---

## 🔧 Component Testing

### **Method 2: UI Only (Offline Testing)**

Test UI components without MCP server running:

```bash
cd /media/hannesn/storage/Code/autogen
poetry run python -m src.autogen_ui.main
```

**Expected Behavior:**
- ✅ UI launches successfully
- ⚠️ Memory tab shows "Memory: Disconnected" (red)
- ✅ All other UI components work (menus, themes, etc.)
- ⚠️ Memory search will show connection errors (expected)

### **Method 3: MCP Server Only**

Test server endpoints independently:

```bash
# Start server
poetry run python -m autogen_mcp.mcp_server

# Test endpoints (new terminal)
curl http://localhost:9000/health
curl -X POST http://localhost:9000/memory/search -H "Content-Type: application/json" -d '{"query": "test", "scope": "conversation", "k": 5}'
```

---

## 📊 What to Test

### **Memory Browser Features**

#### **1. Connection Status**
- **Green "Connected"**: MCP server running → Memory integration working
- **Red "Disconnected"**: No server → UI gracefully handles offline mode

#### **2. Search Functionality**
- **Query Input**: Enter search terms
- **Scope Selection**: conversation/project/global
- **Results Limit**: 1-100 entries
- **Threshold**: 0.0-0.9 similarity threshold
- **Search Results**: Populated tree view with entries

#### **3. Memory Tree View**
- **Columns**: Content (truncated), Scope, Score, Date
- **Selection**: Click entries to view details
- **Scrolling**: Large result sets should scroll properly

#### **4. Details Panel**
- **Content Tab**: Full text content of selected memory
- **Metadata Tab**: ID, score, timestamp, and custom metadata

#### **5. Statistics Panel**
- **Entries Count**: Total memory entries
- **Memory Usage**: MB of memory used
- **Health Status**: System health indicator
- **Real-time Updates**: Statistics refresh every 10 seconds

#### **6. Menu Integration**
- **Memory → Browser**: Should switch to Memory tab
- **Memory → Connect**: Should attempt connection
- **Memory → Statistics**: Should show memory stats

### **Integration Testing**

#### **7. Hybrid Integration**
Our memory service supports 3 modes:

**Direct Mode** (fastest):
- Direct Python imports to MCP components
- No HTTP overhead
- 0-5ms response times

**HTTP Mode** (flexible):
- REST API calls to MCP server
- Network overhead
- 10-50ms response times

**Hybrid Mode** (best of both):
- Tries direct first, falls back to HTTP
- Automatic failover
- Configurable per component

#### **8. Error Handling**
Test various failure scenarios:
- Server not running → Should show disconnected status
- Network errors → Should show error messages
- Invalid queries → Should handle gracefully
- Large datasets → Should paginate properly

---

## 🐛 Troubleshooting

### **Common Issues**

#### **"Memory: Disconnected" (Red Status)**
```bash
# Check if MCP server is running
ps aux | grep "mcp_server"

# Check server logs
poetry run python -m autogen_mcp.mcp_server
```

#### **Import Errors**
```bash
# Test imports
poetry run python -c "from src.autogen_ui.widgets.memory_browser import MemoryBrowserWidget; print('OK')"
poetry run python -c "from src.autogen_ui.services import MemoryService; print('OK')"
```

#### **Search Not Working**
- Check MCP server is running on port 9000
- Verify Qdrant database is accessible
- Check server logs for errors

#### **UI Crashes**
```bash
# Check for Python errors in terminal
# Look for Qt/PySide6 warnings
# Check memory usage with large datasets
```

### **Performance Testing**

#### **Memory Usage**
```bash
# Monitor memory usage while running
top -p $(pgrep -f "autogen_ui")
```

#### **Response Times**
- Direct integration: < 5ms
- HTTP integration: < 50ms
- Large searches: < 500ms

#### **Concurrent Operations**
- Multiple searches should queue properly
- UI should remain responsive during operations
- Background timers should not conflict

---

## 📈 Expected Results

### **✅ Success Indicators**

#### **MCP Server**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9000
```

#### **UI Launch**
```
INFO - [UI] AutoGen Desktop UI Starting
INFO - [UI] MainWindow initialized successfully
INFO - [UI] Memory service initialized with direct integration
INFO - [UI] AutoGen Desktop UI started successfully
```

#### **Memory Connection**
```
INFO - [UI] Memory: Connected
INFO - [UI] Memory service initialized with direct integration
INFO - [UI] Memory stats updated: {'total_entries': 42, 'memory_usage': {'total_mb': 15.2}}
```

### **⚠️ Expected Warnings**

#### **Without MCP Server**
```
WARNING - [UI] HTTP request failed: All connection attempts failed
ERROR - [UI] Failed to get memory stats: All connection attempts failed
```

#### **Qt Deprecation Warnings** (harmless)
```
DeprecationWarning: Enum value 'Qt::ApplicationAttribute.AA_EnableHighDpiScaling' is marked as deprecated
```

---

## 🎯 Test Scenarios

### **Scenario 1: Happy Path**
1. Start MCP server ✅
2. Launch UI ✅
3. Memory tab shows "Connected" ✅
4. Search returns results ✅
5. Statistics update automatically ✅

### **Scenario 2: Offline Mode**
1. Launch UI without server ✅
2. Memory tab shows "Disconnected" ✅
3. UI remains functional ✅
4. Error handling graceful ✅

### **Scenario 3: Server Recovery**
1. Start UI without server
2. Start MCP server
3. Click "Refresh" in memory tab
4. Should reconnect automatically

### **Scenario 4: Large Dataset**
1. Populate memory with many entries
2. Test search performance
3. Test pagination/scrolling
4. Verify UI responsiveness

---

## 🔍 Manual Testing Checklist

### **UI Components**
- [ ] Window launches and renders properly
- [ ] Memory tab loads without errors
- [ ] Search controls are functional
- [ ] Tree view displays correctly
- [ ] Details panel shows content
- [ ] Statistics panel updates
- [ ] Menu items work properly
- [ ] Theme switching works
- [ ] Window resizing works
- [ ] Dock panels can be moved

### **Memory Integration**
- [ ] Connection status accurate
- [ ] Search functionality works
- [ ] Results display properly
- [ ] Error handling graceful
- [ ] Performance acceptable
- [ ] Real-time updates work
- [ ] Memory statistics accurate
- [ ] Health monitoring works

### **Integration Modes**
- [ ] Direct integration works (when available)
- [ ] HTTP integration works (fallback)
- [ ] Hybrid mode switches correctly
- [ ] Automatic fallback functions
- [ ] Error recovery works

---

**🎉 Ready to test! Start with Method 1 (Full Integration Test) for the complete experience.**
