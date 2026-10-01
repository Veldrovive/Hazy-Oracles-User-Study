import os
import time
import requests

API_URL = "http://localhost:8000/api/v1"
API_KEY = os.getenv("API_KEY", "your-api-key")
COLLECTION_ID = "human-ai-asker"
AI_NAME = "example_asker_ai"

def poll_and_respond():
    headers = {"x-api-key": API_KEY}
    
    # 1. Poll for samples
    response = requests.get(
        f"{API_URL}/ai/task/samples",
        params={"collection_id": COLLECTION_ID, "ai_name": AI_NAME, "ai_role": "asker"},
        headers=headers
    )
    if response.status_code != 200:
        print(f"Error fetching samples: {response.text}")
        return
        
    samples = response.json().get("data", [])
    if not samples:
        print("No samples available. Waiting...")
        return
        
    # 2. Iterate and submit responses
    for sample in samples:
        print(f"Submitting response for sample: {sample['sample_id']} (Root: {sample['root_id']}, Node: {sample['node_code']})")
        payload = {
            "collection_id": COLLECTION_ID,
            "root_id": sample["root_id"],
            "ai_name": AI_NAME,
            "node_code": sample["node_code"],
            "response_data": {
                "response_type": "question_asker",
                "previous_answer_meaningful_score": None,
                "current_guess": "I'm not sure yet.",
                "confidence_score": 50,
                "next_question": "Can you elaborate on that?"
            }
        }
        res = requests.post(f"{API_URL}/ai/task/response", json=payload, headers=headers)
        if res.status_code == 200:
            print("Successfully submitted response.")
        else:
            print(f"Failed to submit: {res.text}")

if __name__ == "__main__":
    while True:
        poll_and_respond()
        time.sleep(5)
