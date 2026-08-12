"""Scraper da Petz.

Estratégia: a Petz coloca no HTML um bloco JSON-LD (schema.org/Product) que já
traz o preço estruturado em offers.price. É o alvo mais estável possível — muito
melhor do que raspar "R$" da tela, que pega recomendações por engano.
"""
import json
import re

import requests

from base import (
    Resultado, baixar_html,
    OK, INDISPONIVEL, ERRO_EXTRACAO, ERRO_REDE,
)

SITE = "petz"

# Captura o conteúdo de cada <script type="application/ld+json">...</script>
_LD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _achar_produto(html: str):
    """Percorre os blocos JSON-LD e devolve o objeto cujo @type é 'Product'."""
    for bloco in _LD_RE.findall(html):
        try:
            dado = json.loads(bloco)
        except json.JSONDecodeError:
            continue
        candidatos = dado if isinstance(dado, list) else [dado]
        for obj in candidatos:
            if isinstance(obj, dict) and str(obj.get("@type", "")).lower() == "product":
                return obj
    return None


def extrair(html: str):
    """Recebe HTML e devolve (preco, preco_de, status).

    Função pura (não faz rede) — por isso dá pra testar offline com HTML salvo.
    """
    produto = _achar_produto(html)
    if not produto:
        return None, None, ERRO_EXTRACAO

    offers = produto.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    preco = offers.get("price")
    preco = float(preco) if preco is not None else None

    # Preço de assinatura (quando existe) entra como referência em preco_de.
    preco_de = None
    espec = offers.get("priceSpecification")
    if isinstance(espec, dict) and espec.get("price") is not None:
        preco_de = float(espec["price"])

    disponivel = "instock" in str(offers.get("availability", "")).lower()

    if preco is None:
        return None, preco_de, ERRO_EXTRACAO
    if not disponivel:
        return None, preco_de, INDISPONIVEL
    return preco, preco_de, OK


def coletar(url: str) -> Resultado:
    """Fluxo completo: baixa + extrai + trata erro de rede. Devolve Resultado."""
    try:
        html = baixar_html(url)
    except requests.RequestException as e:
        return Resultado(SITE, url, status=ERRO_REDE, obs=str(e)[:150])
    preco, preco_de, status = extrair(html)
    return Resultado(SITE, url, preco=preco, preco_de=preco_de, status=status)
