import os
import json
import logging
import argparse
from typing import List
from dotenv import load_dotenv

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_dynamic_prompts() -> List[str]:
    """Recupera contexto do Pinecone e usa um LLM para gerar 3 prompts/iscas dinâmicas."""
    try:
        from pinecone import Pinecone
        from langchain_community.retrievers import PineconeHybridSearchRetriever
        from backend.rag.sparse_encoder import FastBM25Encoder
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import PromptTemplate
        
        # 1. Configurar Embeddings e Retriever Híbrido
        index_name = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")
        embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            huggingfacehub_api_token=os.environ.get("HF_TOKEN")
        )
        
        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        index = pc.Index(index_name)
        bm25_encoder = FastBM25Encoder()
        
        retriever = PineconeHybridSearchRetriever(
            embeddings=embeddings,
            sparse_encoder=bm25_encoder,
            index=index,
            top_k=10
        )
        
        # 2. Buscar contexto genérico de "assuntos recentes e polêmicos"
        query = "projeto de lei polêmico votação orçamento emendas escândalo cota parlamentar"
        docs = retriever.invoke(query)
        
        if not docs:
            logging.warning("Nenhum documento retornado do Pinecone.")
            return []
            
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 3. Chamar LLM para gerar os prompts
        # Usando OpenRouter (ou OpenAI fallback)
        llm = ChatOpenAI(
            model=os.environ.get("LLM_MODEL", "google/gemini-2.5-flash"),
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        prompt = PromptTemplate.from_template(
            "Você é um analista político investigativo brasileiro. "
            "Com base no contexto de dados legislativos e de transparência abaixo, "
            "elabore exatamente 3 perguntas (iscas) altamente curiosas e provocativas "
            "que instiguem um usuário a perguntar ao nosso chatbot RAG.\n\n"
            "Regras:\n"
            "- As perguntas devem ser concisas, focadas em correlações atípicas, gastos suspeitos ou votações divergentes.\n"
            "- Não numere as perguntas.\n"
            "- Retorne APENAS as 3 perguntas, uma por linha.\n\n"
            "Contexto Extraído:\n{context}\n\nPerguntas:"
        )
        
        chain = prompt | llm
        result = chain.invoke({"context": context_text[:4000]}) # Limita o contexto para economizar tokens
        
        # Processa resultado
        linhas = [linha.strip() for linha in result.content.split('\n') if linha.strip()]
        # Filtra para evitar introduções do modelo
        perguntas = [p for p in linhas if p.endswith("?")]
        
        return perguntas[:3]
        
    except Exception as e:
        logging.error(f"Erro ao gerar prompts dinâmicos: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Gera prompts dinâmicos baseados no Pinecone")
    parser.add_argument("--output", type=str, default="../../backend/api/curated_prompts.json", help="Caminho do JSON de saída")
    args = parser.parse_args()
    
    load_dotenv()
    
    # 1. Carrega prompts originais para fallback/manter uma base
    output_path = os.path.abspath(args.output)
    
    prompts_atuais = []
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            prompts_atuais = json.load(f)
            
    # 2. Gera novos prompts
    logging.info("Iniciando geração de prompts dinâmicos via LLM...")
    novos_prompts = get_dynamic_prompts()
    
    if novos_prompts:
        logging.info(f"Gerados {len(novos_prompts)} novos prompts. Atualizando arquivo.")
        # Mantém 5 do pool anterior e insere os 3 novos no topo
        pool_atualizado = novos_prompts + prompts_atuais[:5]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pool_atualizado, f, ensure_ascii=False, indent=4)
        logging.info("Arquivo atualizado com sucesso!")
    else:
        logging.warning("Nenhum prompt gerado. O arquivo não foi modificado.")

if __name__ == "__main__":
    main()
