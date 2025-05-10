import requests
import json

url = "http://localhost:8000/query"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
data = {
    "query": "What is the greatest capability of the DuploCloud platform?"
}

response = requests.post(url, headers=headers, json=data)
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2)) 