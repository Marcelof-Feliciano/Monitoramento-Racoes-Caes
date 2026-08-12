"""Testa a EXTRAÇÃO (não a rede) dos scrapers contra HTML real capturado."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))

import petz, petlove

aqui = os.path.dirname(__file__)

# --- Petz ---
html_petz = open(os.path.join(aqui, "petz_produto.html"), encoding="utf-8").read()
preco, preco_de, status = petz.extrair(html_petz)
print(f"[PETZ]    preco={preco}  preco_de={preco_de}  status={status}")
assert preco == 381.99, "Petz: preço esperado 381.99"
assert status == "OK"

# --- Petlove: deve pegar o ALVO (370.32), NUNCA os vizinhos (204.90 / 741.98) ---
html_pl = open(os.path.join(aqui, "petlove_produto.html"), encoding="utf-8").read()
sku = petlove._sku_da_url("https://www.petlove.com.br/racao-.../p?sku=31027540335")
preco, preco_de, status = petlove.extrair(html_pl, sku)
print(f"[PETLOVE] sku={sku}  preco={preco}  preco_de={preco_de}  status={status}")
assert preco == 370.32, f"Petlove: esperado 370.32, veio {preco} (pegou produto errado!)"
assert status == "OK"

# --- Petlove: simular produto esgotado ---
html_out = html_pl.replace('"price":"370.32","priceValidUntil":"2026-08-12T15:07:03.000Z","availability":"https://schema.org/InStock"',
                           '"price":"370.32","availability":"https://schema.org/OutOfStock"')
preco, preco_de, status = petlove.extrair(html_out, sku)
print(f"[PETLOVE-esgotado] preco={preco}  status={status}")
assert status == "INDISPONIVEL" and preco is None

# --- Petz: simular layout mudado (sem JSON-LD) ---
preco, preco_de, status = petz.extrair("<html><body>sem json-ld aqui</body></html>")
print(f"[PETZ-layout-mudou] preco={preco}  status={status}")
assert status == "ERRO_EXTRACAO" and preco is None

print("\nTODOS OS TESTES DE EXTRACAO PASSARAM ✓")
