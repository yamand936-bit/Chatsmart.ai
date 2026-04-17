import os
import glob

# All tsx files
files = glob.glob('frontend/src/**/*.tsx', recursive=True) + glob.glob('frontend/src/**/*.ts', recursive=True)

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the typical absolute URLs with relative ones
    new_content = content.replace("`${process.env.NEXT_PUBLIC_API_URL || ''}/api", "`/api")
    new_content = new_content.replace("`${process.env.NEXT_PUBLIC_API_URL}/api", "`/api")
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Patched: {filepath}")
