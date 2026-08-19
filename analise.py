"""analise.py — gera um painel HTML com a evolução dos preços.

Lê storage/historico.csv e cria storage/relatorio.html: um gráfico interativo
por produto (uma linha por site) + um resumo de variação. Abre o arquivo no
navegador ao final.

Não precisa instalar nada: usa só a biblioteca padrão do Python. O gráfico é
desenhado com Chart.js, carregado de um CDN (precisa de internet só para ABRIR
o relatório).

Uso:
    python analise.py
"""
import csv
import json
import os
import webbrowser
from collections import defaultdict
from datetime import datetime

RAIZ = os.path.dirname(__file__)
HISTORICO = os.path.join(RAIZ, "storage", "historico.csv")
SAIDA = os.path.join(RAIZ, "storage", "relatorio.html")

# Cores fixas por site (pra cada site ter sempre a mesma cor no gráfico)
CORES = {
    "petz": "#e8590c",
    "petlove": "#1c7ed6",
    "cobasi": "#2f9e44",
}
COR_PADRAO = "#868e96"


def carregar():
    """Lê o CSV e devolve só as leituras válidas (status OK e preço numérico)."""
    if not os.path.exists(HISTORICO):
        return []
    linhas = []
    with open(HISTORICO, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "OK" or not row.get("preco"):
                continue
            try:
                preco = float(row["preco"])
            except ValueError:
                continue
            linhas.append({
                "dia": row["data_hora"][:10],          # YYYY-MM-DD
                "produto_id": row["produto_id"],
                "nome": row.get("nome") or row["produto_id"],
                "site": row["site"],
                "preco": preco,
            })
    return linhas


def organizar(linhas):
    """Agrupa por produto. Para cada produto: lista de dias e, por site, o preço
    de cada dia (o ÚLTIMO preço coletado naquele dia)."""
    # ultimo preco por (produto, site, dia)
    ultimo = {}
    nomes = {}
    for l in linhas:
        chave = (l["produto_id"], l["site"], l["dia"])
        ultimo[chave] = l["preco"]  # como o CSV é cronológico, o último sobrescreve
        nomes[l["produto_id"]] = l["nome"]

    produtos = defaultdict(lambda: {"dias": set(), "sites": defaultdict(dict)})
    for (pid, site, dia), preco in ultimo.items():
        produtos[pid]["dias"].add(dia)
        produtos[pid]["sites"][site][dia] = preco

    # montar estrutura final ordenada
    resultado = []
    for pid, dados in produtos.items():
        dias = sorted(dados["dias"])
        series = []
        for site, por_dia in sorted(dados["sites"].items()):
            valores = [por_dia.get(d) for d in dias]  # None onde não coletou
            presentes = [v for v in valores if v is not None]
            series.append({
                "site": site,
                "cor": CORES.get(site, COR_PADRAO),
                "valores": valores,
                "menor": min(presentes) if presentes else None,
                "maior": max(presentes) if presentes else None,
                "atual": next((v for v in reversed(valores) if v is not None), None),
            })
        resultado.append({
            "produto_id": pid,
            "nome": nomes.get(pid, pid),
            "dias": dias,
            "series": series,
        })
    return resultado


def html(produtos):
    """Monta o HTML final com os dados embutidos e o gráfico Chart.js."""
    dados_json = json.dumps(produtos, ensure_ascii=False)
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")
    return TEMPLATE.replace("__DADOS__", dados_json).replace("__GERADO__", gerado)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor de Rações — Painel</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root { color-scheme: light; }
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 0; background: #f4f6f8; color: #222; }
  header { background: #1a1a2e; color: #fff; padding: 20px 24px; }
  header h1 { margin: 0; font-size: 20px; }
  header small { opacity: .7; }
  main { max-width: 980px; margin: 0 auto; padding: 24px 16px 60px; }
  .card { background: #fff; border-radius: 12px; padding: 20px;
          margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  .card h2 { margin: 0 0 4px; font-size: 17px; }
  .card .pid { color: #888; font-size: 12px; margin-bottom: 14px; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; }
  th { color: #666; font-weight: 600; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
  .var-alta { color: #c92a2a; font-weight: 700; }
  .barato { background:#ebfbee; }
  .vazio { text-align:center; color:#999; padding:40px; }
  canvas { margin-top: 8px; }
</style></head>
<body>
<header>
  <h1>🐾 Monitor de Rações — Painel de Preços</h1>
  <small>Gerado em __GERADO__</small>
</header>
<main id="app"></main>
<script>
const PRODUTOS = __DADOS__;
const app = document.getElementById("app");
const brl = v => v==null ? "—" : "R$ " + v.toFixed(2).replace(".", ",");

if (!PRODUTOS.length) {
  app.innerHTML = '<div class="card vazio">Nenhum dado válido no histórico ainda.<br>Rode <b>python main.py</b> algumas vezes e volte aqui.</div>';
}

PRODUTOS.forEach((p, i) => {
  const card = document.createElement("div");
  card.className = "card";

  // menor preço atual entre os sites (destaque de "mais barato hoje")
  const atuais = p.series.map(s => s.atual).filter(v => v!=null);
  const menorAtual = atuais.length ? Math.min(...atuais) : null;

  let linhas = p.series.map(s => {
    const variou = (s.menor!=null && s.maior!=null && s.menor>0)
                 ? ((s.maior - s.menor) / s.menor * 100) : 0;
    const ehBarato = (s.atual!=null && s.atual===menorAtual);
    const classeVar = variou >= 5 ? "var-alta" : "";
    return `<tr class="${ehBarato?'barato':''}">
      <td><span class="dot" style="background:${s.cor}"></span>${s.site}${ehBarato?' 🏆':''}</td>
      <td>${brl(s.atual)}</td>
      <td>${brl(s.menor)}</td>
      <td>${brl(s.maior)}</td>
      <td class="${classeVar}">${variou.toFixed(1).replace('.',',')}%</td>
    </tr>`;
  }).join("");

  card.innerHTML = `
    <h2>${p.nome}</h2>
    <div class="pid">${p.produto_id} • ${p.dias.length} dia(s) coletado(s)</div>
    <canvas id="c${i}" height="120"></canvas>
    <table>
      <thead><tr><th>Site</th><th>Atual</th><th>Menor</th><th>Maior</th><th>Variação</th></tr></thead>
      <tbody>${linhas}</tbody>
    </table>`;
  app.appendChild(card);

  new Chart(document.getElementById("c"+i), {
    type: "line",
    data: {
      labels: p.dias.map(d => d.slice(8,10)+"/"+d.slice(5,7)),
      datasets: p.series.map(s => ({
        label: s.site, data: s.valores, borderColor: s.cor,
        backgroundColor: s.cor, tension: .25, spanGaps: true, pointRadius: 3,
      })),
    },
    options: {
      responsive: true,
      plugins: { tooltip: { callbacks: { label: ctx => ctx.dataset.label+": "+brl(ctx.parsed.y) } } },
      scales: { y: { ticks: { callback: v => "R$ "+v } } },
    },
  });
});
</script>
</body></html>
"""


def main():
    linhas = carregar()
    produtos = organizar(linhas)
    conteudo = html(produtos)
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"Relatorio gerado: {SAIDA}")
    print(f"Produtos: {len(produtos)} | Leituras validas: {len(linhas)}")
    try:
        webbrowser.open("file://" + os.path.abspath(SAIDA))
    except Exception:
        pass


if __name__ == "__main__":
    main()
