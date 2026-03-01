#!/usr/bin/env python3
import json, re, requests

URL = "https://ecqvyfsxaofboilnlkna.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcXZ5ZnN4YW9mYm9pbG5sa25hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjM4OTEzMiwiZXhwIjoyMDg3OTY1MTMyfQ.mZspN6Yvm4I6K0ur8oMKGx0GGm0BztXDcUJ4z5PDluw"
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

with open('data/tools.json') as f:
    data = json.load(f)

# Insert categories
print("Inserting categories...")
cat_map = {}  # slug -> uuid
for i, cat in enumerate(data['categories']):
    slug = cat['id']
    payload = {
        "name": cat['name'],
        "emoji": cat['icon'],
        "description": cat['description'],
        "slug": slug,
        "sort_order": i
    }
    r = requests.post(f"{URL}/rest/v1/categories", headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        result = r.json()
        cat_map[slug] = result[0]['id'] if isinstance(result, list) else result['id']
        print(f"  ✓ {cat['name']}")
    else:
        print(f"  ✗ {cat['name']}: {r.status_code} {r.text}")

print(f"\nInserted {len(cat_map)} categories")

# Insert tools in batches per category
total = 0
for cat in data['categories']:
    cat_id = cat_map.get(cat['id'])
    if not cat_id:
        print(f"Skipping tools for {cat['name']} - no category ID")
        continue
    
    tools_batch = []
    for tool in cat['tools']:
        slug = slugify(tool['name'])
        tools_batch.append({
            "name": tool['name'],
            "url": tool['url'],
            "description": tool['desc'],
            "category_id": cat_id,
            "featured": tool.get('featured', False),
            "status": "active",
            "slug": slug
        })
    
    r = requests.post(f"{URL}/rest/v1/tools", headers=HEADERS, json=tools_batch)
    if r.status_code in (200, 201):
        total += len(tools_batch)
        print(f"  ✓ {cat['name']}: {len(tools_batch)} tools")
    else:
        # Try one by one for duplicate slug issues
        for tool in tools_batch:
            r2 = requests.post(f"{URL}/rest/v1/tools", headers=HEADERS, json=tool)
            if r2.status_code in (200, 201):
                total += 1
            else:
                # Add category prefix to slug
                tool['slug'] = f"{cat['id']}-{tool['slug']}"
                r3 = requests.post(f"{URL}/rest/v1/tools", headers=HEADERS, json=tool)
                if r3.status_code in (200, 201):
                    total += 1
                else:
                    print(f"    ✗ {tool['name']}: {r3.status_code} {r3.text[:100]}")

print(f"\nTotal tools inserted: {total}")
