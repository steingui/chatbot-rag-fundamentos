import os
import logging
import re
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")

_retriever = None
_llm = None
_session_agents = {}
_session_sources = {}

def init_components():
    global _retriever, _llm
    if not os.environ.get("PINECONE_API_KEY"):
        raise ValueError("PINECONE_API_KEY não configurada no .env!")

    logging.info(f"Conectando ao Pinecone (Index: {INDEX_NAME}) e ao LLM...")
    
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    _retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    _llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openai_api_base=OPENROUTER_BASE,
        max_retries=10,
        temperature=0.2
    )

def _consultar_pinecone(query: str, session_id: str = "default") -> str:
    if _retriever is None:
        return "Erro: retriever não inicializado."
    docs = _retriever.invoke(query)
    if session_id not in _session_sources:
        _session_sources[session_id] = []
    
    formatted_texts = []
    for doc in docs:
        _session_sources[session_id].append(doc)
        src = doc.metadata.get("source", "Desconhecido")
        formatted_texts.append(f"[Fonte: {src}]\n{doc.page_content}")
    
    return "\n\n".join(formatted_texts) if formatted_texts else "Nenhum documento relevante encontrado na base interna."

def _buscar_noticias_web(query: str, session_id: str = "default") -> str:
    try:
        search_tool = DuckDuckGoSearchResults(num_results=5)
        results_str = search_tool.run(query)
        
        urls = re.findall(r'link:\s*(https?://[^\s,]+)', results_str)
        if session_id not in _session_sources:
            _session_sources[session_id] = []
        for url in urls:
            _session_sources[session_id].append(Document(page_content=url, metadata={"source": url}))
            
        return results_str
    except Exception as e:
        logging.error(f"Erro no DuckDuckGo: {e}")
        return "Não foi possível obter notícias recentes da web no momento."

class AgentWrapper:
    def __init__(self, agent_executor: AgentExecutor, session_id: str):
        self.agent_executor = agent_executor
        self.session_id = session_id

    def invoke(self, inputs: dict) -> dict:
        question = inputs.get("question", "")
        _session_sources[self.session_id] = []
        
        result = self.agent_executor.invoke({"input": question})
        answer = result.get("output", "")
        
        sources = _session_sources.get(self.session_id, [])
        return {
            "answer": answer,
            "source_documents": sources
        }

def get_rag_chain(session_id: str = "default"):
    if _llm is None:
        init_components()

    if session_id in _session_agents:
        return _session_agents[session_id]

    tools = [
        Tool(
            name="consultar_base_politica",
            func=lambda q: _consultar_pinecone(q, session_id),
            description="Busca documentos oficiais de votações da Câmara dos Deputados, bens do TSE e checagens de fatos da Lupa."
        ),
        Tool(
            name="buscar_noticias_web",
            func=lambda q: _buscar_noticias_web(q, session_id),
            description="Busca notícias políticas recentes e atualizações na web via DuckDuckGo."
        )
    ]

    template = """Você é um assistente sênior especializado em política brasileira e dados legislativos.
Responda à pergunta do usuário consultando a base de dados interna ou buscando na web quando necessário. Se ambas trouxerem dados, faça o merge sintetizando as informações de forma coesa.
REGRA CRÍTICA: Se perguntado sobre nomes, listas ou valores específicos e não houver comprovação exata nas ferramentas, NUNCA invente dados. Diga explicitamente o que encontrou.

Você tem acesso às seguintes ferramentas:

{tools}

Para usar uma ferramenta, use EXATAMENTE o seguinte formato:

Thought: Você deve sempre pensar sobre o que fazer
Action: a ação a tomar, deve ser uma de [{tool_names}]
Action Input: a entrada para a ação
Observation: o resultado da ação
... (este Thought/Action/Action Input/Observation pode se repetir N vezes)
Thought: Eu agora sei a resposta final
Final Answer: a resposta final para a pergunta do usuário

Instrução de início:

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)
    agent = create_react_agent(_llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )

    wrapper = AgentWrapper(agent_executor, session_id)
    _session_agents[session_id] = wrapper
    return wrapper

def iniciar_chat() -> None:
    print("\nAgente Politico RAG + Web conectado. Digite 'sair' para encerrar.")
    while True:
        try:
            user_input = input("\nVocê: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit"]:
                break

            chain = get_rag_chain("cli-session")
            response = chain.invoke({"question": user_input})
            print(f"\nBot: {response['answer']}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Erro: {e}")

def main() -> None:
    try:
        iniciar_chat()
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
