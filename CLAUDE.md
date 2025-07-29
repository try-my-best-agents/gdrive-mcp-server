# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Package Management
- Use `uv` for Python package management
- `uv init` - Initialize new Python project
- `uv add <package>` - Add dependencies
- `uv sync` - Install dependencies
- `uv run <command>` - Run commands in virtual environment

### Build and Development
- `uv run gdrive-mcp-server --service-account /path/to/credentials.json` - Start the HTTP MCP server on port 8000
- `uv run gdrive-test-server --service-account /path/to/credentials.json` - Start the test HTTP server on port 8001

### Testing
- HTTP endpoints:
  - Main server: `http://localhost:8000/mcp-servers/gdrive-mcp-server/`
  - Test server: `http://localhost:8001/mcp-servers/gdrive-test-server/`
- Use HTTP clients or configure MCP clients to connect to these endpoints

## Architecture

This is a Model Context Protocol (MCP) server that provides Google Drive integration for AI applications. The server follows MCP protocol specifications using FastMCP.

### Core Components

**Python implementation using FastMCP:**
- FastMCP server with HTTP transport (Streamable HTTP)
- Runs on localhost-only (127.0.0.1) for security
- Main server on port 8000, test server on port 8001
- Google Drive API client using google-api-python-client
- Service account authentication via command-line argument
- Async tool and resource handlers for Drive operations

**Key MCP capabilities:**
- **Resources**: Lists and reads Google Drive files via `gdrive:///{file_id}` URIs
- **Tools**: 
  - `gdrive_search` - Full-text search across Drive files
  - `gdrive_read_file` - Read file contents by ID with format conversion

**File format handling:**
- Google Docs → Markdown export
- Google Sheets → CSV export  
- Google Presentations → Plain text
- Google Drawings → PNG images
- Text/JSON files → UTF-8 text
- Other files → Base64 encoded

### Authentication Flow

1. Service account credentials JSON file passed via `--service-account` argument
2. Server initializes Google Drive service with read-only scope
3. No OAuth2 flow required - direct service account authentication

### Configuration

**Command-line arguments:**
- `--service-account` - Path to Google service account JSON file (required)

**Environment variables:**
- `FOLDER_ID` - Optional Google Drive folder ID to limit searches to a specific folder and its subfolders

**Client integration:**
Server runs as HTTP service, typically configured in MCP client as:
```json
{
  "url": "http://localhost:8000/mcp-servers/gdrive-mcp-server/",
  "transport": "http",
  "env": {
    "FOLDER_ID": "your-folder-id-here"
  }
}
```

**Nginx proxy configuration example:**
```nginx
location /mcp-servers/gdrive-mcp-server/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Dependencies

- `fastmcp` - FastMCP framework for building MCP servers
- `google-api-python-client` - Google Drive API client
- `google-auth` - Google authentication library
- `google-auth-httplib2` - HTTP transport for Google auth

## Development Notes

- Python 3.10+ project managed with uv
- Async/await pattern for tools and resources
- Error handling returns tool errors in result format rather than raising exceptions
- Search queries are escaped and wrapped in `fullText contains` Drive API syntax
- File reading handles both export (Google Workspace) and download (regular files) APIs