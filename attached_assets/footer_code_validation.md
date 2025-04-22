# Footer Campaign Code Validation Guide

## Overview

The footer campaign code validation feature allows you to verify that the correct campaign code and country code are present in the footer of your marketing emails. This helps ensure consistency between your email metadata, UTM parameters, and the campaign information visible to recipients.

## Supported Formats

The validation system supports various formats of campaign codes:

1. **Standard Format**: `CODE - COUNTRY`
   - Example: `ABC2505 - US` or `XYZ2505 - MX`
   - Includes spaces around the dash

2. **Compact Format**: `CODE-COUNTRY`
   - Example: `ABC2505-US` or `XYZ2505-MX`
   - No spaces around the dash

3. **Prefixed Format**: `PREFIX_CODE - COUNTRY` or `PREFIX_CODE-COUNTRY`
   - Example: `123_ABC2505 - US` or `456_XYZ2505-MX`
   - The validation will ignore any numeric prefix before an underscore

## How to Use

In your requirements JSON file, the system will use the `campaign_code` and `country` fields to validate the footer:

```json
{
  "campaign_code": "ABC2505",
  "country": "US",
  // other validation requirements...
}
```

The actual campaign code should appear somewhere in the footer section of your email HTML, typically in the format:

```html
<p>... Campaign Code: ABC2505 - US ...</p>
```

The validation system will:
1. Extract the campaign code and country code from both the expected and actual values
2. Handle various formatting differences (spacing, prefixes, etc.)
3. Compare the core campaign code and country code for an exact match

## Handling of Prefixes

If your campaign tracking includes variable prefixes (e.g., `123_ABC2505`), the system will:

1. Extract the part after the underscore (`ABC2505`)
2. Use this extracted value for comparison
3. Ignore any differences in prefixes

This allows for flexibility in how campaign codes are tracked internally while ensuring the core campaign identifier is validated correctly.

## Best Practices

1. Always include the campaign code in the footer of your emails in a consistent format
2. Use the same core campaign code in UTM parameters and footer references
3. When setting up validation requirements, use the standardized format with spaces: `CODE - COUNTRY`