# Project Structure

The gdrive-mcp-server is organized with a modular architecture for better maintainability and extensibility.

## Directory Structure

```
src/gdrive_mcp_server/
├── __init__.py
├── server.py           # Main server entry point
├── test_server.py      # Test server with additional tools
├── tools/              # MCP tools
│   ├── __init__.py
│   ├── drive.py        # Google Drive tools (search, read)
│   └── sheets.py       # Google Sheets tools (expense tracking)
└── resources/          # MCP resources
    ├── __init__.py
    └── drive.py        # Google Drive resource handlers
```

## Module Descriptions

### `server.py`
Main entry point for the production MCP server. Runs on port 8000 with HTTP transport.
- Initializes Google Drive service with service account
- Registers Drive tools and resources
- Provides basic Drive functionality (search, read)

### `test_server.py`
Extended server for testing and development. Runs on port 8001.
- Includes all production server features
- Additional tools for folder management
- Google Sheets tools for expense tracking
- Used for testing new features

### `tools/drive.py`
Core Google Drive tools:
- `gdrive_search`: Search files in Drive
- `gdrive_read_file`: Read file contents with format conversion

### `tools/sheets.py`
Google Sheets tools for expense tracking:
- `create_expense_sheet`: Create formatted expense tracking sheets
- `read_sheet_cells`: Read data from sheets
- `update_sheet_cells`: Update sheet data
- `append_expense_row`: Add expense entries
- `set_sheet_metadata`: Store custom properties
- `get_sheet_metadata`: Retrieve custom properties
- `add_category_validation`: Add dropdown validations
- `get_expense_summary`: Generate expense reports

### `resources/drive.py`
MCP resource handlers:
- `gdrive:///{file_id}`: Access Drive files as MCP resources

## Registration Pattern

Each module exports a registration function that takes the MCP server instance and Drive service:

```python
def register_drive_tools(mcp: FastMCP, drive_service: Any) -> None:
    """Register tools with the MCP server."""
    
    @mcp.tool()
    async def tool_name(...):
        # Tool implementation
```

This pattern allows for:
- Clean separation of concerns
- Easy addition of new tools/resources
- Shared service instances
- Consistent error handling

## Adding New Features

To add new tools or resources:

1. Create a new module in the appropriate directory
2. Implement the registration function
3. Import and call the registration in server.py or test_server.py
4. Document the new features

Example:
```python
# tools/calendar.py
def register_calendar_tools(mcp: FastMCP, drive_service: Any) -> None:
    @mcp.tool()
    async def create_calendar_event(...):
        # Implementation
```