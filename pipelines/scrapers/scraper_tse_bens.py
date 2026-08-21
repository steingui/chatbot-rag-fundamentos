import os
import json
import logging
from pathlib import Path

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
DOCS_DIR = Path("data/docs")

# Mock de dados do TSE para fins didáticos/MVP
# Em produção, usaria a API do DivulgaCand (ex: /divulga/rest/v1/candidatura/buscar/2022/BR/204060/candidato/{id}/bens)
CANDIDATOS_MOCK = [
    {
        "id": "1",
        "nome": "João Fictício",
        "partido": "PEX",
        "cargo": "Deputado Federal",
        "total_bens": 1500000.00,
        "bens": [
            {"descricao": "Apartamento em São Paulo", "valor": 1200000.00},
            {"descricao": "Veículo SUV 2021", "valor": 300000.00}
        ],
        "maiores_doadores": [
            {"nome": "Empresa Fictícia Agronegócio", "valor": 50000.00},
            {"nome": "Diretório Nacional PEX", "valor": 200000.00}
        ]
    },
    {
        "id": "2",
        "nome": "Maria Exemplo",
        "partido": "PEX2",
        "cargo": "Senadora",
        "total_bens": 500000.00,
        "bens": [
            {"descricao": "Casa na Praia", "valor": 450000.00},
            {"descricao": "Ações da Petrobras", "valor": 50000.00}
        ],
        "maiores_doadores": [
            {"nome": "Sindicato Nacional X", "valor": 10000.00},
            {"nome": "Diretório Estadual PEX2", "valor": 100000.00}
        ]
    }
]

def format_bens_md(candidato: dict) -> str:
    """Formata os dados patrimoniais e financeiros do candidato em Markdown."""
    nome = candidato["nome"]
    cargo = candidato["cargo"]
    partido = candidato["partido"]
    
    md_lines = [
        f"[TEMA: FINANCIAMENTO E BENS - {nome}]",
        f"# Declaração de Bens e Financiamento: {nome} ({partido})",
        f"\n**Cargo Disputado:** {cargo}",
        f"**Patrimônio Total Declarado:** R$ {candidato['total_bens']:,.2f}",
        "\n## Detalhamento de Bens\n"
    ]
    
    for bem in candidato["bens"]:
        md_lines.append(f"- **{bem['descricao']}**: R$ {bem['valor']:,.2f}")
        
    md_lines.append("\n## Maiores Doadores de Campanha\n")
    for doador in candidato["maiores_doadores"]:
        md_lines.append(f"- **{doador['nome']}**: R$ {doador['valor']:,.2f}")
        
    return "\n".join(md_lines)

def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Iniciando extração de Bens e Financiamentos (TSE Mock)...")
    
    for candidato in CANDIDATOS_MOCK:
        cand_id = candidato["id"]
        logging.info(f"Processando candidato: {candidato['nome']}")
        
        md_content = format_bens_md(candidato)
        
        filepath = DOCS_DIR / f"tse_bens_cand_{cand_id}.md"
        filepath.write_text(md_content, encoding="utf-8")
        logging.info(f"Arquivo gerado: {filepath}")
        
    logging.info("Scraping TSE (Bens) concluído!")

if __name__ == "__main__":
    main()
