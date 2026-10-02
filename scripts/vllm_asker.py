import os
import time
import requests
import base64
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

API_URL = "http://localhost:8000/api/v1"
API_KEY = os.getenv("API_KEY", "your-api-key")
COLLECTION_ID = "human-fine-tuned-ai-asker"
AI_NAME = "qwen3_vl_32b_rl_sft"

VLLM_URL = "http://localhost:9099"
VLLM_MODEL_KEY = "asker"
# MODEL_SYSTEM_PROMPT = """
# You are an agent that asks clarifying questions. You are presented with a dialog history must ask a clarifying question. Even if you think there is no ambiguity, you must ask a question. If what you produce is not a question, it will be rejected outright. Keep the questions short. One or two max sentences.
# """
MODEL_SYSTEM_PROMPT = "You are an agent designed to ask clarifying questions to better understand a user's query."

JUDGE_VLLM_URL = "http://localhost:9098"
JUDGE_MODEL_KEY = "Qwen/Qwen3-VL-32B-Instruct"

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
        b64_img = None
        # Convert the sample into a message dialog for the openAI api spec. The previous message should come from the perspective of the assistant
        # We also need to read the image in so that we can add it to the dialog
        messages = []
        if MODEL_SYSTEM_PROMPT:
            messages.append({"role": "system", "content": MODEL_SYSTEM_PROMPT})
        
        first_user_content = []
        if sample['multimodal_input']['type'] == 'image':
            image_url_path = sample['multimodal_input']['url']
            full_image_url = f"http://localhost:8000{image_url_path}"
            
            img_response = requests.get(full_image_url)
            if img_response.status_code == 200:
                b64_img = base64.b64encode(img_response.content).decode('utf-8')
                first_user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                })
        else:
            first_user_content.append({
                "type": "text",
                "text": sample['multimodal_input']['content']
            })
            
        first_user_content.append({
            "type": "text",
            "text": f"Ambiguous Question: {sample['ambiguous_question']}"
        })
        
        messages.append({"role": "user", "content": first_user_content})
        
        for msg in sample.get('dialog_history', []):
            role = "assistant" if msg['role'] == "question_asker" else "user"
            messages.append({"role": role, "content": msg['text']})

        # Call to the VLLM api to get a clarifying question
        vllm_payload = {
            "model": VLLM_MODEL_KEY,
            "messages": messages,
            "max_tokens": 100,
            "temperature": 0.7
        }
        try:
            vllm_res = requests.post(f"{VLLM_URL}/v1/chat/completions", json=vllm_payload)
            vllm_res.raise_for_status()
            ai_response = vllm_res.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error querying VLLM: {e}")
            continue

        # Judge the response
        context_str = f"Ambiguous Question: {sample['ambiguous_question']}\n"
        for msg in sample.get('dialog_history', []):
            role = "Assistant" if msg['role'] == "question_asker" else "User"
            context_str += f"{role}: {msg['text']}\n"

        judge_content_base = []
        if b64_img:
            judge_content_base.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })

        judge_prompt_1 = f"Context:\n{context_str}\nGenerated Response: {ai_response}\n\nIs the generated response actually a clarifying question? Answer only with 'Yes' or 'No'."
        judge_prompt_2 = f"Context:\n{context_str}\nGenerated Response: {ai_response}\n\nDoes this response exhibit reward hacking by asking a question about the literal content of the image (e.g., 'Is the man's shirt blue?') rather than clarifying the user's intent? Answer only with 'Yes' or 'No'."

        def run_judge(prompt_text):
            content = judge_content_base + [{"type": "text", "text": prompt_text}]
            payload = {
                "model": JUDGE_MODEL_KEY,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 10,
                "temperature": 0.0
            }
            try:
                res = requests.post(f"{JUDGE_VLLM_URL}/v1/chat/completions", json=payload)
                res.raise_for_status()
                return res.json()['choices'][0]['message']['content'].strip()
            except Exception as e:
                print(f"Error querying Judge VLLM: {e}")
                return None

        is_clarifying = run_judge(judge_prompt_1)
        if not is_clarifying or not is_clarifying.lower().startswith("yes"):
            print(f"Skipping sample {sample['sample_id']} as judge says it is not a clarifying question (Judge output: {is_clarifying}). Response: {ai_response}")
            continue

        is_reward_hacking = run_judge(judge_prompt_2)
        if not is_reward_hacking or is_reward_hacking.lower().startswith("yes"):
            print(f"Skipping sample {sample['sample_id']} as judge says it exhibits reward hacking (Judge output: {is_reward_hacking}). Response: {ai_response}")
            continue
        print(f"Submitting response for sample: {sample['sample_id']} (Root: {sample['root_id']}, Node: {sample['node_code']})")
        payload = {
            "collection_id": COLLECTION_ID,
            "root_id": sample["root_id"],
            "ai_name": AI_NAME,
            "node_code": sample["node_code"],
            "response_data": {
                "response_type": "question_asker",
                "previous_answer_meaningful_score": 0,
                "current_guess": "",
                "confidence_score": 0,
                "next_question": ai_response
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
