import os
import logging
from typing import List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

DEFAULT_MODELS_FALLBACK_ORDER = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free"
]

class DynamicFallbackLLMManager:
    """Gerenciador dinâmico de resiliência e fallback entre múltiplos provedores/modelos de LLM."""

    def __init__(self, primary_model: Optional[str] = None):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.primary_model = primary_model or DEFAULT_MODELS_FALLBACK_ORDER[0]
        self.fallback_models = [m for m in DEFAULT_MODELS_FALLBACK_ORDER if m != self.primary_model]

    def get_llm_instance(self, model_name: str) -> BaseChatModel:
        return ChatOpenAI(
            model=model_name,
            openai_api_key=self.api_key or "sk-dummy",
            openai_api_base="https://openrouter.ai/api/v1",
            max_retries=1,
            request_timeout=30.0,
            temperature=0.2
        )

    def invoke_with_fallback(self, prompt_input: Any) -> Any:
        models_to_try = [self.primary_model] + self.fallback_models
        last_exception = None

        for model_name in models_to_try:
            try:
                logging.info(f"Tentando invocação de LLM com modelo: {model_name}")
                llm = self.get_llm_instance(model_name)
                res = llm.invoke(prompt_input)
                return res
            except Exception as e:
                logging.warning(f"Falha ao invocar LLM no modelo {model_name}: {e}. Acionando fallback...")
                last_exception = e

        raise RuntimeError(f"Todos os provedores de LLM falharam: {last_exception}")
