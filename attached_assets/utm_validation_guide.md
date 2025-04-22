# UTM Campaign Code Validation Guide

## Special UTM Campaign Handling

The Email QA system now includes special validation logic for the `utm_campaign` parameter. This is because marketing campaigns often include variable prefixes in the campaign parameter that indicate whether an email is a test send or a live send.

### Format of UTM Campaign Values

UTM campaign values often follow this format:
```
{variable_prefix}_{campaign_code}
```

Where:
- `variable_prefix`: A number or code that varies between test/live sends (e.g., "0_", "1_", "123_")
- `campaign_code`: The actual campaign identifier that remains consistent (e.g., "ABC2505")

### How to Specify Requirements

When specifying your requirements in JSON, you have two options:

#### Option 1: Use the Full Pattern with Prefix

```json
{
  "utm_parameters": {
    "utm_campaign": "0_ABC2505"
  }
}
```

The validation will intelligently extract the campaign code after the underscore ("ABC2505") and only validate that portion.

#### Option 2: Use Only the Campaign Code

```json
{
  "utm_parameters": {
    "utm_campaign": "ABC2505"
  }
}
```

In this case, the validation will still work correctly with email links that contain prefixes (like "0_ABC2505").

### Examples of Valid Matches

With a requirement of `utm_campaign": "ABC2505"`, all of the following link values would pass validation:

- `utm_campaign=ABC2505`
- `utm_campaign=0_ABC2505`
- `utm_campaign=123_ABC2505`

### Examples of Invalid Matches

With a requirement of `utm_campaign": "ABC2505"`, these would fail validation:

- `utm_campaign=DIFFERENT2505`
- `utm_campaign=0_XYZ2505`
- `utm_campaign=ABC2506` (different campaign code)

## Practical Application

This feature is particularly useful when testing emails that may be sent in different environments (test vs. production) but should maintain the same core campaign identifier regardless of the environment prefix.