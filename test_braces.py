import requests
import json

# Test generation with description that needs variables
desc = 'Analyze a support ticket message and draft an empathetic response.'
r = requests.post('http://127.0.0.1:5000/api/workflows/generate',
    json={'name':'Support Response Generator', 'description': desc}, timeout=60)

print('Generation Status:', r.status_code)
if r.status_code == 200:
    d = r.json()
    print('Steps generated:', len(d.get('steps', [])))
    for i, step in enumerate(d.get('steps', [])):
        prompt = step.get('prompt','')
        has_double = '{{' in prompt
        has_single = '{' in prompt and '{{' not in prompt
        print(f'\nStep {i+1}: {step.get("id")}')
        print(f'  Double braces {{ }}: {has_double}')
        print(f'  Single braces {{ }}: {has_single}')
        if has_double:
            print('  ❌ ERROR: Found {{ }} - should be {')
        elif has_single:
            print('  ✅ OK: Using single braces')
        if prompt:
            print(f'  Prompt: {prompt[:100]}...')
else:
    print('Error:', r.json())

