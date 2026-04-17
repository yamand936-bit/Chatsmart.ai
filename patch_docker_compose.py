with open('docker-compose.yml', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace NEXT_PUBLIC_API_URL default
text = text.replace('NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}', 'NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-}')
text = text.replace('- NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}', '- NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-}')

with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write(text)
