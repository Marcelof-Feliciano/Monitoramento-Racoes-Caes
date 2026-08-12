"""main.py — o coração do projeto.

Fluxo a cada execução:
  1. Lê config.json (a lista de produtos e fontes).
  2. Para cada fonte, chama o scraper certo (petz/petlove/cobasi).
  3. Grava UMA linha por fonte no storage/historico.csv, com data, status etc.

Regras de robustez:
  - Um site que falha NÃO derruba os outros (cada coleta é isolada).
  - Preço "sem valor" vira vazio + status; NUNCA 0.
  - O arquivo de histórico só cresce (append) — é a sua série temporal.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

import petz
import petlove
import cobasi
from base import Resultado, ERRO_EXTRACAO

# Mapa: nome do site no config -> módulo que sabe raspar aquele site
SCRAPERS = {
    "petz": petz,
    "petlove": petlove,
    "cobasi": cobasi,
}

RAIZ = os.path.dirname(__file__)
CONFIG = os.path.join(RAIZ, "config.json")
HISTORICO = os.path.join(RAIZ, "storage", "historico.csv")

COLUNAS = ["data_hora", "produto_id", "site", "sku", "url", "preco", "preco_de", "status", "obs"]


def identificar_sku(site: str, url: str) -> str:
    """Extrai o identificador único do produto na URL de cada site."""
    if site == "petlove":
        m = re.search(r"[?&]sku=([^&]+)", url)
        return m.group(1) if m else ""
    # petz e cobasi: numero no fim da URL
    m = re.search(r"-(\d+)(?:$|[/?#])", url)
    return m.group(1) if m else ""


def linha_do_resultado(produto_id: str, r: Resultado) -> dict:
    """Monta a linha (dict) que vai pro CSV. preco vazio quando None (nunca 0)."""
    return {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "produto_id": produto_id,
        "site": r.site,
        "sku": identificar_sku(r.site, r.url),
        "url": r.url,
        "preco": "" if r.preco is None else f"{r.preco:.2f}",
        "preco_de": "" if r.preco_de is None else f"{r.preco_de:.2f}",
        "status": r.status,
        "obs": r.obs,
    }


def salvar(linhas: list):
    """Anexa as linhas ao historico.csv, criando o cabeçalho na 1a vez."""
    os.makedirs(os.path.dirname(HISTORICO), exist_ok=True)
    novo = not os.path.exists(HISTORICO)
    with open(HISTORICO, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        if novo:
            w.writeheader()
        w.writerows(linhas)


def coletar_tudo(config: dict) -> list:
    """Percorre o config e devolve a lista de linhas coletadas."""
    linhas = []
    for produto in config.get("produtos", []):
        pid = produto["produto_id"]
        for fonte in produto.get("fontes", []):
            site, url = fonte["site"], fonte["url"]
            modulo = SCRAPERS.get(site)
            if modulo is None:
                r = Resultado(site, url, status=ERRO_EXTRACAO, obs="site sem scraper cadastrado")
            else:
                try:
                    r = modulo.coletar(url)
                except Exception as e:  # blindagem extra: nada derruba a coleta inteira
                    r = Resultado(site, url, status=ERRO_EXTRACAO, obs=f"excecao: {e}"[:150])
            linhas.append(linha_do_resultado(pid, r))
    return linhas


def main():
    with open(CONFIG, encoding="utf-8") as f:
        config = json.load(f)

    linhas = coletar_tudo(config)
    salvar(linhas)

    # Resumo no console (útil quando rodar manualmente)
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] {len(linhas)} coleta(s):")
    for l in linhas:
        preco = f"R$ {l['preco']}".replace(".", ",") if l["preco"] else "(sem valor)"
        print(f"  {l['produto_id']:40} {l['site']:8} {l['status']:14} {preco}")
    print(f"Gravado em: {HISTORICO}")


if __name__ == "__main__":
    main()
