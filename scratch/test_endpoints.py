import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app
import json

client = app.test_client()

print("--- Testing Routes ---")
for route in ['/', '/explore', '/dashboard', '/about', '/compare']:
    res = client.get(route)
    print(f"Route {route}: status {res.status_code}")
    assert res.status_code == 200, f"Route {route} failed with {res.status_code}"

print("\n--- Testing API /api/companies ---")
res = client.get('/api/companies?page=1&limit=25')
print(f"API status: {res.status_code}")
data = json.loads(res.data)
print(f"Total companies returned in API: {data['total']}")
print(f"Page size: {len(data['companies'])}")
print("First 5 companies:")
for c in data['companies'][:5]:
    print("  ", c)

print("\n--- Testing Ahmedabad filter (Screenshot 2 & 3) ---")
res = client.get('/api/companies?location=Ahmedabad&page=1&limit=10')
data = json.loads(res.data)
print(f"Ahmedabad total matching: {data['total']}")
print("Top 10 in Ahmedabad:")
for c in data['companies'][:10]:
    print(f"   {c['company_name']} | * {c['company_rating']} | {c['industry']} | {c['size']} | {c['type']} | {c['age']} | {c['location']}")

print("\n--- Testing API Search ---")
res = client.get('/api/search?q=tcs')
search_data = json.loads(res.data)
print(f"TCS search matches: {len(search_data)}")

print("\n--- ALL TESTS PASSED! ---")
