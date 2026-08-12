# 🐾 Monitoramento de Rações para Cães

Monitor de preços de rações em pet shops brasileiros. Coleta o preço dos mesmos
produtos, todos os dias, em vários sites, e guarda um histórico para você
descobrir se existe uma "época" do mês/ano em que o valor varia bastante — e,
mais adiante, ser avisado quando um preço cair bem abaixo do praticado.

Roda **100% em segundo plano**, sem abrir navegador: fala direto com o servidor
de cada site via HTTP.

---

## Como funciona

A cada execução, o programa:

1. Lê o `config.json` (a sua lista de produtos e onde monitorá-los).
2. Para cada fonte, chama o scraper do site correspondente.
3. Grava **uma linha por fonte** no `storage/historico.csv`, com data, preço e status.

O preço é sempre lido de uma **fonte estruturada** amarrada ao identificador único
do produto (SKU/ID) — nunca "o primeiro R$ da página". Isso evita pegar o preço de
um produto recomendado por engano.

Quando algo dá errado, o histórico **não** grava `0`: grava o campo de preço vazio
mais um **status** que diz o que aconteceu. Assim a análise nunca é contaminada.

| status          | significado                                                        |
|-----------------|--------------------------------------------------------------------|
| `OK`            | preço lido normalmente                                             |
| `INDISPONIVEL`  | site respondeu, mas o produto estava esgotado/sem preço           |
| `ERRO_EXTRACAO` | baixou a página, mas não achou o preço (o layout pode ter mudado) |
| `ERRO_REDE`     | não conseguiu nem baixar (bloqueio, timeout, sem internet)        |

---

## Sites suportados

| Site        | Como o preço é obtido                                             |
|-------------|------------------------------------------------------------------|
| **Petz**    | JSON-LD (`schema.org/Product`) embutido no HTML                  |
| **Petlove** | JSON embutido no HTML, ancorado no `sku` exato da URL            |
| **Cobasi**  | API pública de catálogo da VTEX (por `productId`)               |

Cada site tem seu próprio arquivo em `scrapers/`, todos com a mesma interface
(`coletar(url) -> Resultado`). Se um site muda o layout, você mexe **só** no
arquivo dele; adicionar um site novo é criar mais um arquivo.

---

## Estrutura

```
.
├── config.json          # sua lista de produtos e fontes (você edita)
├── main.py              # orquestra: lê config, roda scrapers, grava histórico
├── testar.py            # teste rápido: bate nos sites e diz se passou/bloqueou
├── run.bat              # atalho para o Agendador de Tarefas do Windows
├── requirements.txt
├── scrapers/
│   ├── base.py          # peças comuns (status, headers, download, Resultado)
│   ├── petz.py
│   ├── petlove.py
│   └── cobasi.py
├── _fixtures/           # HTML real + teste offline dos parsers
│   ├── teste_parsers.py
│   ├── petz_produto.html
│   └── petlove_produto.html
├── storage/             # criada sozinha; aqui nasce o historico.csv (fora do Git)
└── logs/                # criada sozinha pelo run.bat (fora do Git)
```

---

## Instalação

Requer Python 3.10+.

```bash
pip install -r requirements.txt
```

---

## Configuração

Edite o `config.json`. Cada produto tem um `produto_id` (nome interno, sem espaços)
e uma lista de `fontes`. Um produto pode estar em quantos sites você quiser — se só
existe em 2 sites, coloque só 2 fontes.

```json
{
  "produtos": [
    {
      "produto_id": "royal_golden_retriever_adulto_10kg",
      "nome": "Royal Canin Golden Retriever Adulto 10,1kg",
      "fontes": [
        { "site": "petz",    "url": "https://www.petz.com.br/produto/....-194370" },
        { "site": "petlove", "url": "https://www.petlove.com.br/....?sku=31027540335" }
      ]
    }
  ]
}
```

> **Dica:** o identificador único vem na própria URL — Petz/Cobasi usam o número no
> final (`-194370`), a Petlove usa o `?sku=`. É só copiar a URL do produto do site.

---

## Como rodar

**Manual (uma vez):**
```bash
python main.py
```

**Teste de conectividade** (verifica se os sites respondem sem bloqueio):
```bash
python testar.py
```

**Teste offline dos parsers** (não usa internet):
```bash
python _fixtures/teste_parsers.py
```

**Agendar no Windows** (todo dia às 14h) — CMD como Administrador:
```cmd
schtasks /Create /TN "Monitor racoes" /TR "\"C:\caminho\do\projeto\run.bat\"" /SC DAILY /ST 14:00 /RL HIGHEST /F
```
Rodar na hora, sem esperar: `schtasks /Run /TN "Monitor racoes"`

> Em Linux/macOS, use o `cron` chamando `python main.py`.

---

## O histórico

`storage/historico.csv` cresce a cada execução (uma linha por produto × fonte):

```
data_hora, produto_id, site, sku, url, preco, preco_de, status, obs
```

`preco_de` guarda o preço "cheio"/de referência quando o site fornece (útil para
detectar promoções). Esse formato já é praticamente um esquema de banco de dados —
migrar para SQLite depois é direto.

---

## Roadmap

- [ ] Gráficos semanais (variação por dia da semana / período do mês)
- [ ] Alerta de preço baixo (limite definido após observar o histórico)
- [ ] Migração de CSV para SQLite
- [ ] Novos produtos e categorias pet

---

## Aviso / uso responsável

Projeto de uso **pessoal** para acompanhamento de preços. Coleta com frequência
baixa (1x/dia por padrão) para não sobrecarregar os sites. Os sites podem mudar
seu layout ou sua API a qualquer momento — quando isso acontecer, o status
`ERRO_EXTRACAO` aponta qual scraper precisa de ajuste. Respeite os termos de uso
de cada site.

---

## Licença

MIT — veja [LICENSE](LICENSE).
