from langchain_community.chat_models import ChatOllama
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from langchain.llms.base import LLM
import requests

from .config import env

def get_llm():
    model = env("OLLAMA_MODEL", "llama3.1")
    base_url = env("OLLAMA_BASE_URL", "http://localhost:11434")

     # --- Quick connectivity test ---
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2)
        if(resp.status_code == 200):
            print(f"Using Ollama model {model} at {base_url}")
            return ChatOllama(model=model, temperature=0.3, base_url=base_url)
        
    except Exception as e:
        
        # fallback to lightweight HF pipeline

        print(f"Ollama not available at {base_url}, falling back to HuggingFace. Error: {e}")

        hf_model = "google/flan-t5-small"
        tokenizer = AutoTokenizer.from_pretrained(hf_model)
        mdl = AutoModelForSeq2SeqLM.from_pretrained(hf_model)
        text_gen = pipeline("text2text-generation" , model=mdl, tokenizer=tokenizer, max_new_tokens=512)

        class HFGen(LLM):
            @property
            def _llm_type(self):
                return "hf-seq2seq"

            def _call(self, prompt: str, stop=None) -> str:
                out = text_gen(prompt)[0]["generated_text"]
                return out

        return HFGen()
