"""Scraper da Cobasi.

Estratégia: a Cobasi roda em VTEX, que expõe uma API pública de catálogo.
Dado o productId (o número no fim da URL, ex: .../racao-...-3696960), consultamos
    /api/catalog_system/pub/products/search?fq=productId:<id>
e lemos o preço em items[0].sellers[0].commertialOffer.

Obs.: hoje a Cobasi NÃO vende a Royal Canin Golden Retriever Adulto (só a Filhote),
então este scraper ainda não é usado no config — fica pronto para quando entrar.
"""
import re

import requests

from base import (
    Resultado, HEADERS,
    OK, INDISPONIVEL, ERRO_EXTRACAO, ERRO_REDE,
)

SITE = "cobasi"
API = "https://www.cobasi.com.br/api/catalog_system/pub/products/search"


def _product_id(url: str):
    """Pega o número final da URL da Cobasi (.../slug-3696960)."""
    m = re.search(r"-(\d+)(?:$|[/?#])", url)
    return m.group(1) if m else None


def extrair(dados: list):
    """Recebe a lista JSON da API e devolve (preco, preco_de, status). Sem rede."""
    if not dados:
        return None, None, ERRO_EXTRACAO
    try:
        oferta = dados[0]["items"][0]["sellers"][0]["commertialOffer"]
    except (KeyError, IndexError, TypeError):
        return None, None, ERRO_EXTRACAO

    preco = oferta.get("Price")
    preco_de = oferta.get("ListPrice")
    disponivel = bool(oferta.get("IsAvailable"))

    preco = float(preco) if preco not in (None, 0) else None
    preco_de = float(preco_de) if preco_de not in (None, 0) else None

    if preco is None:
        return None, preco_de, INDISPONIVEL if not disponivel else ERRO_EXTRACAO
    if not disponivel:
        return None, preco_de, INDISPONIVEL
    return preco, preco_de, OK


def coletar(url: str) -> Resultado:
    pid = _product_id(url)
    if not pid:
        return Resultado(SITE, url, status=ERRO_EXTRACAO, obs="productId nao encontrado na URL")
    try:
        resp = requests.get(API, params={"fq": f"productId:{pid}"},
                            headers={**HEADERS, "Accept": "application/json"}, timeout=20)
        resp.raise_for_status()
        dados = resp.json()
    except requests.RequestException as e:
        return Resultado(SITE, url, status=ERRO_REDE, obs=str(e)[:150])
    except ValueError as e:
        return Resultado(SITE, url, status=ERRO_EXTRACAO, obs=f"resposta nao-JSON: {e}")
    preco, preco_de, status = extrair(dados)
    return Resultado(SITE, url, preco=preco, preco_de=preco_de, status=status)
