# Google Drive MIME Types Reference

This document provides a comprehensive reference for MIME types used in the Google Drive API.

## Google Workspace Native MIME Types

These are the native MIME types for Google Workspace applications:

| MIME Type | Description |
|-----------|-------------|
| `application/vnd.google-apps.audio` | Audio file |
| `application/vnd.google-apps.document` | Google Docs |
| `application/vnd.google-apps.drawing` | Google Drawings |
| `application/vnd.google-apps.drive-sdk` | Third-party shortcut |
| `application/vnd.google-apps.file` | Google Drive file |
| `application/vnd.google-apps.folder` | Google Drive folder |
| `application/vnd.google-apps.form` | Google Forms |
| `application/vnd.google-apps.fusiontable` | Google Fusion Tables |
| `application/vnd.google-apps.jam` | Google Jamboard |
| `application/vnd.google-apps.mail-layout` | Email layout |
| `application/vnd.google-apps.map` | Google My Maps |
| `application/vnd.google-apps.photo` | Google Photos |
| `application/vnd.google-apps.presentation` | Google Slides |
| `application/vnd.google-apps.script` | Google Apps Script |
| `application/vnd.google-apps.shortcut` | Shortcut |
| `application/vnd.google-apps.site` | Google Sites |
| `application/vnd.google-apps.spreadsheet` | Google Sheets |
| `application/vnd.google-apps.unknown` | Unknown file type |
| `application/vnd.google-apps.vid` | Google Vids |
| `application/vnd.google-apps.video` | Video file |

## Export MIME Types

Google Workspace documents can be exported to various formats. Here are the common export mappings used in this MCP server:

| Google Workspace Type | Export Format | Export MIME Type |
|----------------------|---------------|------------------|
| Google Docs (`application/vnd.google-apps.document`) | Markdown | `text/markdown` |
| Google Sheets (`application/vnd.google-apps.spreadsheet`) | CSV | `text/csv` |
| Google Slides (`application/vnd.google-apps.presentation`) | Plain Text | `text/plain` |
| Google Drawings (`application/vnd.google-apps.drawing`) | PNG | `image/png` |

### Additional Export Options

Google Workspace documents support multiple export formats. Common alternatives include:

**Google Docs:**
- `application/pdf` - PDF
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Microsoft Word (.docx)
- `application/rtf` - Rich Text Format
- `text/html` - HTML
- `text/plain` - Plain text
- `application/epub+zip` - EPUB

**Google Sheets:**
- `application/pdf` - PDF
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` - Microsoft Excel (.xlsx)
- `text/tab-separated-values` - TSV
- `application/vnd.oasis.opendocument.spreadsheet` - OpenDocument Spreadsheet

**Google Slides:**
- `application/pdf` - PDF
- `application/vnd.openxmlformats-officedocument.presentationml.presentation` - Microsoft PowerPoint (.pptx)
- `image/png` - PNG (exports current slide)
- `image/jpeg` - JPEG (exports current slide)
- `image/svg+xml` - SVG (exports current slide)

## Usage in the MCP Server

The gdrive-mcp-server automatically handles the conversion of Google Workspace files when reading:
- Files are exported using the mappings defined in the server code
- Binary files that cannot be converted to text are returned as base64-encoded content
- The server indicates the encoding type in the response (`utf-8` or `base64`)

## References

- [Google Drive API MIME Types](https://developers.google.com/workspace/drive/api/guides/mime-types)
- [Export MIME Types for Google Workspace](https://developers.google.com/workspace/drive/api/guides/ref-export-formats)