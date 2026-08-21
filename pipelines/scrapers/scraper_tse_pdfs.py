import os
import logging
from pathlib import Path

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
DOCS_DIR = Path("data/docs")

# Mock de Planos de Governo já pós-processados pelo LLM (Refinamento)
# Em produção, usaria PyPDF2/pdfplumber -> langchain LLMChain para resumir e limpar
PLANOS_MOCK = [
    {
        "id": "1",
        "candidato": "João Fictício",
        "partido": "PEX",
        "ano": "2026",
        "resumo_llm": (
            "1. **Economia:** Propõe a redução de impostos corporativos e incentivo ao agronegócio.\n"
            "2. **Saúde:** Construção de 50 novos hospitais regionais.\n"
            "3. **Educação:** Foco na educação técnica e militarização de escolas públicas."
        )
    },
    {
        "id": "2",
        "candidato": "Maria Exemplo",
        "partido": "PEX2",
        "ano": "2026",
        "resumo_llm": (
            "1. **Economia:** Criação de renda básica universal e taxação de grandes fortunas.\n"
            "2. **Saúde:** Fortalecimento do SUS com repasse de 20% do PIB.\n"
            "3. **Meio Ambiente:** Zerar o desmatamento até 2030 e incentivos a energia limpa."
        )
    }
]

def refine_and_save_pdfs() -> None:
    """Simula a extração de PDFs e o refinamento via LLM, salvando em Markdown."""
    for plano in PLANOS_MOCK:
        cand_id = plano["id"]
        candidato = plano["candidato"]
        
        logging.info(f"Processando plano de governo (PDF/LLM Refinement): {candidato}")
        
        md_content = (
            f"[TEMA: PLANO DE GOVERNO - {candidato}]\n"
            f"# Plano de Governo: {candidato} ({plano['partido']} - {plano['ano']})\n\n"
            f"**Resumo Oficial Extraído (Refinado por IA):**\n\n"
            f"{plano['resumo_llm']}\n"
        )
        
        filepath = DOCS_DIR / f"tse_plano_cand_{cand_id}.md"
        filepath.write_text(md_content, encoding="utf-8")
        logging.info(f"Arquivo gerado: {filepath}")

def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Iniciando pipeline do TSE (Planos de Governo - PDFs)...")
    refine_and_save_pdfs()
    logging.info("Pipeline TSE (Planos) concluída.")

if __name__ == "__main__":
    main()
