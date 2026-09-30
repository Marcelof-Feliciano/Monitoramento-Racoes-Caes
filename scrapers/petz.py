"""Scraper da Petz.

Fonte principal: a meta tag OpenGraph
    <meta property="product:price:amount" content="...">
traz o preço do item selecionado na página. Ela existe tanto em produto simples
quanto em produto com variações (ProductGroup) — por isso é o alvo mais estável.
Também usamos product:availability (disponibilidade) e, quando houver,
product:original_price:amount (preço "de").

Fonte reserva: se a meta não vier, caímos no JSON-LD (schema.org/Product), que
cobre as páginas antigas de ração.
"""
import json
import re

import requests

from base import (
    Resultado, baixar_html,
    OK, INDISPONIVEL, ERRO_EXTRACAO, ERRO_REDE,
)

SITE = "petz"

_LD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _meta(html: str, prop: str):
    """Lê o content de uma <meta property="..."> (aceita as duas ordens de atributos)."""
    m = re.search(r'<meta[^>]+(?:property|name)="' + re.escape(prop) + r'"[^>]+content="([^"]*)"',
                  html, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="' + re.escape(prop) + r'"',
                      html, re.IGNORECASE)
    return m.group(1) if m else None


def _para_float(txt):
    if txt is None:
        return None
    try:
        return float(str(txt).replace(",", "."))
    except ValueError:
        return None


def _achar_produto_ld(html: str):
    """Reserva: primeiro objeto JSON-LD cujo @type é 'Product'."""
    for bloco in _LD_RE.findall(html):
        try:
            dado = json.loads(bloco)
        except json.JSONDecodeError:
            continue
        for obj in (dado if isinstance(dado, list) else [dado]):
            if isinstance(obj, dict) and str(obj.get("@type", "")).lower() == "product":
                return obj
    return None


def extrair(html: str):
    """Recebe HTML e devolve (preco, preco_de, status). Sem rede — testável offline."""
    preco = _para_float(_meta(html, "product:price:amount"))
    preco_de = _para_float(_meta(html, "product:original_price:amount"))

    disponivel = None
    disp_meta = _meta(html, "product:availability")
    if disp_meta is not None:
        disponivel = "instock" in disp_meta.replace("_", "").lower()

    # Reserva: JSON-LD, se a meta não trouxe preço
    if preco is None:
        prod = _achar_produto_ld(html)
        if prod:
            offers = prod.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            preco = _para_float(offers.get("price"))
            if disponivel is None:
                disponivel = "instock" in str(offers.get("availability", "")).lower()

    if preco is None:
        return None, preco_de, ERRO_EXTRACAO
    if disponivel is False:
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
