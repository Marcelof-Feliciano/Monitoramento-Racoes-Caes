"""TESTE AO VIVO — rode este arquivo na SUA máquina.

Ele bate nos sites de verdade e diz, para cada um, se:
  - passou (OK / INDISPONIVEL)  -> o modo leve (sem navegador) funciona
  - tomou bloqueio (ERRO_REDE)  -> pode precisar do plano B (Playwright)
  - achou a página mas nao o preço (ERRO_EXTRACAO) -> o layout mudou

Como rodar:
    pip install requests
    python testar.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

import petz
import petlove

# As suas duas fontes confirmadas (mesmo produto, 10,1kg)
ALVOS = [
    ("Petz",    petz,    "https://www.petz.com.br/produto/racao-royal-canin-para-caes-adultos-da-raca-golden-retriever-10-1kg-194370"),
    ("Petlove", petlove, "https://www.petlove.com.br/racao-royal-canin-para-caes-adultos-da-raca-golden-retriever/p?sku=31027540335"),
]

def interpretar(status: str) -> str:
    return {
        "OK": "passou — modo leve funciona",
        "INDISPONIVEL": "passou (produto esgotado no momento)",
        "ERRO_REDE": "BLOQUEIO/rede — talvez precise do plano B (Playwright)",
        "ERRO_EXTRACAO": "baixou, mas nao achou o preço — layout pode ter mudado",
    }.get(status, status)

print("Testando os dois sites ao vivo...\n")
for nome, modulo, url in ALVOS:
    r = modulo.coletar(url)
    preco = f"R$ {r.preco:.2f}".replace(".", ",") if r.preco is not None else "(sem valor)"
    print(f"{nome:8} | {r.status:14} | {preco:16} | {interpretar(r.status)}")
    if r.obs:
        print(f"         └─ detalhe: {r.obs}")

print("\nSe os dois vierem OK, seguimos para o main.py + planilha + agendamento.")
