import requests
import streamlit as st

def generate_commentary(prompt: str) -> str:
    """Routes LLM generation between cloud providers (Groq) and local Ollama with fallback."""
    
    # 1. Check for Cloud API Key (e.g., Groq via st.secrets)
    if "groq" in st.secrets and "api_key" in st.secrets["groq"]:
        try:
            groq_api_key = st.secrets["groq"]["api_key"]
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
        except Exception:
            pass  # Fallback to local if cloud request fails

    # 2. Try Local Ollama endpoint
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('response', '')
    except Exception:
        pass  # Fallback to hardcoded safety string

    return ""
