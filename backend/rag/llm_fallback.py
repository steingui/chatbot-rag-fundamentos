import os
import logging
from typing import List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

DEFAULT_MODELS_FALLBACK_ORDER = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "qwen/qwen-2.5-coder-32b-instruct:free"
]

class DynamicFallbackLLMManager:
    """Gerenciador dinâmico de resiliência e fallback entre múltiplos provedores/modelos de LLM usando LangChain with_fallbacks."""

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

    def get_resilient_chain(self) -> Any:
        primary = self.get_llm_instance(self.primary_model)
        fallbacks = [self.get_llm_instance(m) for m in self.fallback_models]
        return primary.with_fallbacks(fallbacks)

    def invoke_with_fallback(self, prompt_input: Any) -> Any:
        resilient_chain = self.get_resilient_chain()
        try:
            logging.info(f"Executando cadeia resiliente com modelo primário: {self.primary_model}")
            return resilient_chain.invoke(prompt_input)
        except Exception as e:
            logging.warning(f"Cadeia resiliente com fallbacks automáticos falhou: {e}. Executando tentativa direta individual...")
            # Fallback manual em caso de erro estrutural nas exceções
            models_to_try = [self.primary_model] + self.fallback_models
            last_exception = e
            for model_name in models_to_try:
                try:
                    llm = self.get_llm_instance(model_name)
                    return llm.invoke(prompt_input)
                except Exception as ex:
                    last_exception = ex
            raise RuntimeError(f"Todos os provedores de LLM falharam: {last_exception}")

