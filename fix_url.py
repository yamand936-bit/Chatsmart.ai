def fix():
    # Fix test_missing.py
    with open('test_missing.py', 'r', encoding='utf-8') as f:
        code = f.read()
    code = code.replace('/api/system/announcement', '/api/system/system/announcement')
    with open('test_missing.py', 'w', encoding='utf-8') as f:
        f.write(code)

    # Fix layout.tsx
    path = 'frontend/src/app/app/layout.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    code = code.replace('/api/system/announcement', '/api/system/system/announcement')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

fix()
print("Fixed URLs")
