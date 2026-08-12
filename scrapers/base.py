"""Peças comuns a todos os scrapers.

A ideia central: cada site tem seu próprio arquivo, mas todos falam a mesma
"língua" — recebem uma URL e devolvem um objeto Resultado padronizado. Assim,
se um site mudar, você mexe só no arquivo dele; o resto do projeto nem sente.
"""
from dataclasses import dataclass
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Status possíveis de uma coleta. Nunca gravamos preço 0 para "sem valor":
# usamos None (vazio) + um destes rótulos, pra não poluir a análise depois.
# ---------------------------------------------------------------------------
OK = "OK"                    # achou o preço normalmente
INDISPONIVEL = "INDISPONIVEL"  # site respondeu, mas o produto está esgotado/sem preço
ERRO_EXTRACAO = "ERRO_EXTRACAO"  # baixou a página, mas não achou o preço (layout mudou?)
ERRO_REDE = "ERRO_REDE"      # não conseguiu nem baixar (bloqueio anti-bot, timeout, offline)

# Cabeçalhos que imitam um navegador real. É a primeira linha de defesa contra
# bloqueio anti-bot quando rodamos "puro" (sem abrir navegador).
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


@dataclass
class Resultado:
    """O que toda coleta devolve, independentemente do site."""
    site: str
    url: str
    preco: Optional[float] = None
    preco_de: Optional[float] = None   # preço "cheio"/referência, quando existir
    status: str = ERRO_EXTRACAO
    obs: str = ""                      # detalhe do erro, quando houver


def baixar_html(url: str, timeout: int = 20) -> str:
    """Baixa o HTML da página. Levanta requests.RequestException em erro de rede/HTTP."""
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text
