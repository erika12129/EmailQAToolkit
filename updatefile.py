#!/usr/bin/env python3
import re

# Read the new function
with open('updatefunction.js', 'r') as f:
    new_function = f.read()

# Read the original file
with open('static/index.html', 'r') as f:
    content = f.read()

# Find and replace the function
pattern = r'function checkSelectedProductTables\(\) \{.*?\.finally\(\(\) => \{[^}]*\}\);[^}]*\}'
replacement = new_function
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content
with open('static/index.html', 'w') as f:
    f.write(new_content)

print("File updated successfully")
