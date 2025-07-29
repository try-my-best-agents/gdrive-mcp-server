# Google Sheets Tools for Expense Tracking

This document describes the Google Sheets tools available in the gdrive-test-server for expense tracking and recordkeeping.

## Overview

The Google Sheets tools are designed specifically for expense tracking and financial recordkeeping. They provide comprehensive functionality for creating, reading, updating, and managing expense data in Google Sheets.

## Available Tools

### 1. `create_expense_sheet`

Creates a new Google Sheet optimized for expense tracking with pre-configured headers, formatting, and validation.

**Parameters:**
- `name` (required): Name for the new spreadsheet
- `folder_id` (optional): Target folder ID (defaults to FOLDER_ID env var)
- `categories` (optional): List of expense categories for dropdown validation
- `initial_headers` (optional): Column headers (defaults to expense tracking headers)

**Default Headers:**
- Date
- Description
- Category
- Amount
- Payment Method
- Notes
- Tags

**Default Categories:**
- Food & Dining
- Transportation
- Shopping
- Bills & Utilities
- Healthcare
- Entertainment
- Travel
- Education
- Personal Care
- Other

**Features:**
- Formatted header row with dark background
- Date column formatted as YYYY-MM-DD
- Amount column formatted as currency
- Category dropdown validation
- Auto-resized columns
- Developer metadata for tracking

### 2. `read_sheet_cells`

Reads cell values from a Google Sheet.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `range_notation` (optional): A1 notation range (default: "A1:Z1000")

**Returns:**
- Spreadsheet title
- Cell values as 2D array
- Row and column counts

### 3. `update_sheet_cells`

Updates cells in a Google Sheet.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `range_notation` (required): A1 notation range (e.g., "A2:D2")
- `values` (required): 2D array of values to write
- `value_input_option` (optional): How to interpret values (default: "USER_ENTERED")

### 4. `append_expense_row`

Appends a new expense row to the sheet with proper formatting.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `date` (required): Date of expense (YYYY-MM-DD format)
- `description` (required): Description of the expense
- `category` (required): Expense category
- `amount` (required): Amount spent
- `payment_method` (optional): Payment method used
- `notes` (optional): Additional notes
- `tags` (optional): Comma-separated tags

### 5. `set_sheet_metadata`

Sets developer metadata on a sheet for tracking custom properties like budget limits or fiscal periods.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `key` (required): Metadata key (e.g., "budget_limit", "fiscal_year")
- `value` (required): Metadata value
- `location_type` (optional): Where to attach metadata ("spreadsheet" or "sheet")

**Use Cases:**
- Store budget limits: `key="budget_2024", value="50000"`
- Track fiscal periods: `key="fiscal_year", value="2024"`
- Store report settings: `key="default_view", value="monthly"`

### 6. `get_sheet_metadata`

Retrieves developer metadata from a sheet.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `key` (optional): Specific key to search for

### 7. `add_category_validation`

Adds dropdown validation to a column for expense categories.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `column` (required): Column letter (e.g., "C")
- `categories` (required): List of allowed categories
- `start_row` (optional): Starting row for validation (default: 2)

**Example:**
```json
{
  "spreadsheet_id": "abc123",
  "column": "C",
  "categories": ["Food", "Transport", "Utilities", "Entertainment"],
  "start_row": 2
}
```

### 8. `get_expense_summary`

Generates a summary of expenses from the sheet, grouped by category.

**Parameters:**
- `spreadsheet_id` (required): The ID of the spreadsheet
- `date_range` (optional): Date range filter (format: "YYYY-MM-DD:YYYY-MM-DD")

**Returns:**
- Total amount spent
- Breakdown by category with amounts and transaction counts
- Total transaction count

## Example Workflows

### Creating a New Expense Tracker

1. Create a new expense sheet:
```json
{
  "name": "Personal Expenses 2024",
  "categories": ["Groceries", "Dining Out", "Gas", "Utilities", "Entertainment"]
}
```

2. Set metadata for the fiscal year:
```json
{
  "spreadsheet_id": "abc123",
  "key": "fiscal_year",
  "value": "2024"
}
```

3. Set a budget limit:
```json
{
  "spreadsheet_id": "abc123",
  "key": "monthly_budget",
  "value": "3000"
}
```

### Recording Daily Expenses

Use `append_expense_row` to add new expenses:
```json
{
  "spreadsheet_id": "abc123",
  "date": "2024-01-15",
  "description": "Grocery shopping at Whole Foods",
  "category": "Groceries",
  "amount": 125.50,
  "payment_method": "Credit Card",
  "notes": "Weekly groceries",
  "tags": "food,essentials"
}
```

### Monthly Reporting

Get expense summary for a specific month:
```json
{
  "spreadsheet_id": "abc123",
  "date_range": "2024-01-01:2024-01-31"
}
```

## Best Practices

1. **Consistent Categories**: Use the same category names across all expense entries for accurate summaries.

2. **Date Format**: Always use YYYY-MM-DD format for dates to ensure proper sorting and filtering.

3. **Metadata Usage**: Store configuration and settings as metadata rather than in cells to keep data clean.

4. **Regular Summaries**: Use `get_expense_summary` regularly to track spending against budgets.

5. **Tags for Flexibility**: Use the tags field for additional categorization that might change over time.

## Integration with MCP Clients

These tools are available through the test server running on port 8001:

```json
{
  "url": "http://localhost:8001/mcp-servers/gdrive-test-server/",
  "transport": "http"
}
```

All tools support the standard MCP request/response format and include comprehensive error handling for common scenarios like permission issues, invalid data, and API limits.