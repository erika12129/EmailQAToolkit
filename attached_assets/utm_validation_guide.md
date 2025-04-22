# UTM Campaign Parameter Validation Guide

## Overview

The UTM campaign parameter validation feature allows you to verify that all links in your marketing emails have the correct UTM parameters, particularly focusing on the `utm_campaign` parameter. This helps ensure consistent tracking across all links in your emails.

## Supported UTM Campaign Formats

The validation system supports various formats of campaign codes in UTM parameters:

1. **Standard Format**: `utm_campaign=CODE`
   - Example: `utm_campaign=ABC2505`

2. **Prefixed Format**: `utm_campaign=PREFIX_CODE`
   - Example: `utm_campaign=123_ABC2505` or `utm_campaign=0_ABC2505`
   - The validation will ignore any prefix before an underscore

## How UTM Campaign Validation Works

When validating UTM campaign parameters, the system:

1. Extracts all links from the email HTML
2. Processes each link to identify UTM parameters
3. For the `utm_campaign` parameter, applies special handling:
   - If the value contains an underscore, it extracts the part after the underscore
   - Compares this extracted value with the expected campaign code (also processed the same way)
4. Reports any discrepancies in the validation results

## Setting Up UTM Validation Requirements

In your requirements JSON file, specify the expected UTM parameters:

```json
{
  "utm_parameters": {
    "utm_source": "abc",
    "utm_campaign": "123_ABC2505",
    "utm_medium": "email"
  }
}
```

## Handling Variable Prefixes

The system is designed to be flexible with campaign tracking that uses variable prefixes:

- If the expected `utm_campaign` value is `123_ABC2505` and a link has `456_ABC2505`, it will still PASS
- This is because the system extracts `ABC2505` from both values and compares only that portion
- The prefix (before underscore) can vary without failing validation

## Integration with Footer Campaign Code Validation

For comprehensive email validation, combine UTM campaign validation with footer campaign code validation:

1. Use the same core campaign code in both your footer and UTM parameters
2. The validation system will extract and compare the core values across both locations
3. This ensures consistency throughout the email

## Best Practices

1. Use a consistent format for UTM campaign parameters across all links
2. When tracking multiple parameters in the campaign code, separate them with underscores (e.g., `123_ABC2505_email`)
3. Match your utm_campaign parameter with the campaign code that appears in the email footer
4. Include UTM parameters on all links, including social media and footer links