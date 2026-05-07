import requests
import json

url = "http://localhost:5000/query"
payload = {"type": "discover", "similar_to": "Cu_ZnO_Al2O3"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
