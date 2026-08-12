"""Scraper da Petlove.

Estratégia: a página traz, no HTML, um bloco por variação (peso) do produto, cada
um com seu "sku" seguido do seu "offers":{...,"price":...}. Como a página também
lista outros produtos (recomendados), NÃO dá pra pegar "o primeiro price".
Ancoramos no SKU exato que vem na URL (.../p?sku=XXXX) e pegamos o offers logo
em seguida. É isso que garante que nunca troquemos o produto pelo vizinho.
"""
import re
from urllib.parse import urlparse, parse_qs

import requests

from base import (
    Resultado, baixar_html,
    OK, INDISPONIVEL, ERRO_EXTRACAO, ERRO_REDE,
)

SITE = "petlove"


def _sku_da_url(url: str):
    """Extrai o sku de uma URL do tipo .../p?sku=31027540335"""
    query = parse_qs(urlparse(url).query)
    return query.get("sku", [None])[0]


def extrair(html: str, sku: str):
    """Recebe HTML + o sku alvo e devolve (preco, preco_de, status).

    Função pura (sem rede) — testável offline.
    """
    if not sku:
        return None, None, ERRO_EXTRACAO

    # Ancora no "sku":"<alvo>" e captura o bloco "offers":{...} imediatamente após.
    padrao = re.compile(
        r'"sku"\s*:\s*"' + re.escape(sku) + r'".*?"offers"\s*:\s*\{(.*?)\}',
        re.DOTALL,
    )
    m = padrao.search(html)
    if not m:
        return None, None, ERRO_EXTRACAO

    bloco_offer = m.group(1)

    preco_m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', bloco_offer)
    preco = float(preco_m.group(1)) if preco_m else None
    disponivel = "instock" in bloco_offer.lower()

    if preco is None:
        return None, None, ERRO_EXTRACAO
    if not disponivel:
        return None, None, INDISPONIVEL
    return preco, None, OK


def coletar(url: str) -> Resultado:
    """Fluxo completo: baixa + extrai + trata erro de rede. Devolve Resultado."""
    sku = _sku_da_url(url)
    try:
        html = baixar_html(url)
    except requests.RequestException as e:
        return Resultado(SITE, url, status=ERRO_REDE, obs=str(e)[:150])
    preco, preco_de, status = extrair(html, sku)
    return Resultado(SITE, url, preco=preco, preco_de=preco_de, status=status)
