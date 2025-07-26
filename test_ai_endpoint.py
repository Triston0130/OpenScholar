#!/usr/bin/env python3
import requests
import json

# Test the AI processing endpoint directly
url = "http://localhost:8000/api/ai/process-collection"

# You'll need to get a valid access token first
# For testing, you can get one by logging in through the UI
access_token = input("Enter your access token (from localStorage): ").strip()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Test data
data = {
    "collection_id": input("Enter collection ID: ").strip(),
    "folder_id": None,
    "ai_config": {
        "api_key": input("Enter OpenAI API key: ").strip(),
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1500,
        "note_types": {
            "summary": True,
            "keyTerms": True,
            "topics": True,
            "methodology": True,
            "findings": True,
            "implications": False
        }
    },
    "process_empty_only": True
}

print("\nSending request to:", url)
print("Headers:", {k: v if k != "Authorization" else "Bearer ***" for k, v in headers.items()})
print("Data:", json.dumps({**data, "ai_config": {**data["ai_config"], "api_key": "***"}}, indent=2))

try:
    response = requests.post(url, headers=headers, json=data, timeout=120)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error!")
        print(response.text)
except requests.exceptions.Timeout:
    print("\nRequest timed out after 120 seconds")
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")