import requests
import os
from datetime import datetime

# URL Base da API da Câmara
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
DOCS_DIR = "docs"

def main():
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    print("Buscando as 5 votações mais recentes da Câmara dos Deputados...")
    
    # 1. Pega as últimas votações
    resp_votacoes = requests.get(f"{BASE_URL}/votacoes", params={
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro",
        "itens": 5
    })
    
    if resp_votacoes.status_code != 200:
        print("Erro ao acessar API da Câmara")
        return

    votacoes = resp_votacoes.json().get("dados", [])
    
    for votacao in votacoes:
        votacao_id = votacao["id"]
        proposicao_obj = votacao.get("proposicaoObjeto")
        sigla = proposicao_obj if proposicao_obj else f"Votação {votacao_id}"
        descricao = votacao.get("descricao", "Sem descrição disponível.")
        data_registro = votacao.get("dataHoraRegistro", "")
        
        print(f"Processando: {sigla} - {votacao_id}")

        # 2. Pega os votos individuais dessa votação
        resp_votos = requests.get(f"{BASE_URL}/votacoes/{votacao_id}/votos")
        if resp_votos.status_code != 200:
            continue
            
        votos = resp_votos.json().get("dados", [])
        if not votos:
            continue
            
        # 3. Formata os dados em Markdown
        md_content = f"# Votação: {sigla}\n\n"
        md_content += f"**Data:** {data_registro}\n\n"
        md_content += f"**Descrição:** {descricao}\n\n"
        md_content += "## Votos dos Deputados\n\n"
        
        for voto in votos:
            deputado = voto["deputado_"]["nome"]
            partido = voto["deputado_"]["siglaPartido"]
            uf = voto["deputado_"]["siglaUf"]
            tipo_voto = voto["tipoVoto"]
            
            md_content += f"- O deputado **{deputado}** ({partido}-{uf}) votou **{tipo_voto}**.\n"
            
        # 4. Salva no diretório docs/
        filename = f"{DOCS_DIR}/votacao_{votacao_id}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"-> Arquivo gerado: {filename}")
        
    print("\nScraping concluído! Rode 'python ingest.py' para vetorizar os novos dados.")

if __name__ == "__main__":
    main()
