import re
with open("C:/Users/yaman/.gemini/antigravity/playground/chatsmartai/seed_demos.py", "r", encoding="utf-8") as f:
    text = f.read()

def escape_arabic(match):
    return match.group(0).encode("unicode_escape").decode("utf-8")

# Escape anything that is non-ascii
text_escaped = "".join([c if ord(c) < 128 else c.encode('unicode_escape').decode('utf-8') for c in text])

with open("C:/Users/yaman/.gemini/antigravity/playground/chatsmartai/seed_demos_ascii.py", "w", encoding="utf-8") as f:
    f.write(text_escaped)
