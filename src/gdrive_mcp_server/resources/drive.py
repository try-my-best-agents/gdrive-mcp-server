"""Google Drive resources for MCP server."""
from typing import Any

from mcp.server.fastmcp import FastMCP


def register_drive_resources(mcp: FastMCP, drive_service: Any) -> None:
    """Register Google Drive resources with the MCP server."""
    
    # We need to access the gdrive_read_file tool that was registered
    # So we'll create our own implementation here
    async def read_file_for_resource(file_id: str):
        """Internal function to read file for resource."""
        # Find the gdrive_read_file tool in the registered tools
        for tool in mcp._tools.values():
            if tool.name == "gdrive_read_file":
                return await tool.fn(file_id=file_id)
        raise RuntimeError("gdrive_read_file tool not found")
    
    @mcp.resource("gdrive:///{file_id}")
    async def read_drive_resource(file_id: str) -> str:
        """
        Read a Google Drive file as an MCP resource.
        
        Args:
            file_id: The ID of the file to read
            
        Returns:
            File content as string
        """
        result = await read_file_for_resource(file_id)
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        content = result.get("content", "")
        encoding = result.get("encoding", "utf-8")
        
        if encoding == "base64":
            return f"[Binary file - Base64 encoded]\n{content}"
        
        return content