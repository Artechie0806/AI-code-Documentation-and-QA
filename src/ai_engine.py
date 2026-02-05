import requests
import json
from typing import List

# --- Configuration ---
# If running locally, Ollama default is http://localhost:11434/v1
# If remote, change this to: http://<YOUR_GPU_SERVER_IP>:11434/v1
API_BASE_URL = "http://localhost:11434/v1" 
GEN_MODEL = "qwen3:4b"  # Or whatever model is loaded on the server
EMBED_MODEL = "nomic-embed-text"

def generate_summary(code: str, chunk_id: str) -> str:
    """
    Sends a POST request to an API endpoint to generate a summary.
    """
    url = f"{API_BASE_URL}/chat/completions"
    
    prompt = f"""
    You are a technical documentation assistant. 
    Analyze the following code chunk ({chunk_id}).
    Provide a indepth and easy to understand sentence, explaining its responsibility.
    Do not explain syntax, just the purpose.
    
    Code:
    {code}
    """
    
    payload = {
        "model": GEN_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # Low temp for factual consistency
        "stream": False
    }

    try:
        # Standard HTTP POST request
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status() # Raise error for 4xx/5xx status codes
        
        # Parse standard OpenAI-compatible JSON response
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
        
    except Exception as e:
        print(f"Error generating summary for {chunk_id}: {e}")
        return "Summary generation failed."

def get_embedding(text: str) -> List[float]:
    """
    Sends a POST request to an API endpoint to get embeddings.
    """
    url = f"{API_BASE_URL}/embeddings"
    
    payload = {
        "model": EMBED_MODEL,
        "input": text
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        # OpenAI format usually returns data[0]['embedding']
        return data['data'][0]['embedding']
        
    except Exception as e:
        print(f"Error embedding text: {e}")
        return []