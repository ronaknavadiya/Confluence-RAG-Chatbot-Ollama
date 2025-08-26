from langchain_community.chat_models import ChatOllama
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.llms.base import LLM

from .config import env

def get_llm():
    model = env("OLLAMA_MODEL", "llama3.1")

    try:
        return ChatOllama(model=model, temperature=0.3)
    except Exception:
        # fallback to lightweight HF pipeline
        smaller_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        tokenizer = AutoTokenizer.from_pretrained(smaller_model)
        mdl = AutoModelForCausalLM.from_pretrained(smaller_model)
        text_gen = pipeline("text-generation" , model=mdl, tokenizer=tokenizer, max_new_tokens=512)

        class HFGen(LLM):
            @property
            def _llm_type(self):
                return "hf-pipeline"

            def _call(self, prompt: str, stop=None) -> str:
                out = text_gen(prompt, do_sample=False)[0]["generated_text"]
                return out[len(prompt):]

        return HFGen()
