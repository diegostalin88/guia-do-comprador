"""Atualiza data/combustivel.json com o preço médio de revenda da ANP (levantamento semanal).

Procura na página da ANP o arquivo .xlsx mais recente do levantamento semanal e lê as abas
de estados e municípios. A ANP às vezes muda nomes de arquivo e colunas; por isso tudo é
procurado por palavras-chave. Se algo falhar, mantém o arquivo anterior e sai sem erro.

Dependência: openpyxl.
"""
import io, json, re, sys, datetime, pathlib, unicodedata, urllib.request

PAGINAS = [
    "https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-do-precos-de-combustiveis-ultimas-semanas-pesquisadas",
    "https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/precos-revenda-e-de-distribuicao-combustiveis/serie-historica-do-levantamento-de-precos",
]
ARQ = pathlib.Path(__file__).resolve().parent.parent / "data" / "combustivel.json"
UF = {"ACRE":"AC","ALAGOAS":"AL","AMAPA":"AP","AMAZONAS":"AM","BAHIA":"BA","CEARA":"CE","DISTRITO FEDERAL":"DF",
      "ESPIRITO SANTO":"ES","GOIAS":"GO","MARANHAO":"MA","MATO GROSSO":"MT","MATO GROSSO DO SUL":"MS","MINAS GERAIS":"MG",
      "PARA":"PA","PARAIBA":"PB","PARANA":"PR","PERNAMBUCO":"PE","PIAUI":"PI","RIO DE JANEIRO":"RJ","RIO GRANDE DO NORTE":"RN",
      "RIO GRANDE DO SUL":"RS","RONDONIA":"RO","RORAIMA":"RR","SANTA CATARINA":"SC","SAO PAULO":"SP","SERGIPE":"SE","TOCANTINS":"TO"}
HDR = {"User-Agent": "Mozilla/5.0 (guia-do-comprador)"}

def sem_acento(s):
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().upper().strip()

def baixar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60) as r:
        return r.read()

def achar_xlsx():
    for pag in PAGINAS:
        try:
            html = baixar(pag).decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            print(f"[aviso] não abri {pag}: {e}")
            continue
        links = re.findall(r'href="([^"]+\.xlsx[^"]*)"', html, flags=re.I)
        semanais = [l for l in links if re.search(r"semanal|resumo|lpc", l, re.I)]
        for l in semanais or links:
            return l if l.startswith("http") else "https://www.gov.br" + l
    return None

def ler_aba(ws):
    linhas = list(ws.iter_rows(values_only=True))
    for i, row in enumerate(linhas[:30]):
        cab = [sem_acento(c) if c is not None else "" for c in row]
        if "PRODUTO" in cab and ("ESTADO" in cab or "MUNICIPIO" in cab):
            idx = {c: j for j, c in enumerate(cab)}
            preco = next((j for c, j in idx.items() if "PRECO MEDIO REVENDA" in c or c == "PRECO MEDIO"), None)
            if preco is None:
                return []
            out = []
            for r in linhas[i + 1:]:
                if r is None or r[preco] in (None, "", "-"):
                    continue
                out.append({"estado": sem_acento(r[idx["ESTADO"]]) if "ESTADO" in idx else "",
                            "municipio": sem_acento(r[idx["MUNICIPIO"]]) if "MUNICIPIO" in idx else "",
                            "produto": sem_acento(r[idx["PRODUTO"]]), "preco": float(r[preco]),
                            "fim": r[idx["DATA FINAL"]] if "DATA FINAL" in idx else None})
            return out
    return []

def main():
    try:
        import openpyxl
    except ImportError:
        print("[aviso] openpyxl não instalado"); return 0
    url = achar_xlsx()
    if not url:
        print("[aviso] não encontrei a planilha semanal da ANP; mantendo dados anteriores"); return 0
    print(f"[info] planilha: {url}")
    try:
        wb = openpyxl.load_workbook(io.BytesIO(baixar(url)), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        print(f"[aviso] não consegui ler a planilha: {e}"); return 0
    atual = json.loads(ARQ.read_text(encoding="utf-8"))
    uf, mun, ref = {}, {}, None
    for ws in wb.worksheets:
        for r in ler_aba(ws):
            prod = "gasolina" if r["produto"] in ("GASOLINA COMUM", "GASOLINA") else "etanol" if r["produto"].startswith("ETANOL") else None
            sigla = UF.get(r["estado"]) or (r["estado"] if len(r["estado"]) == 2 else None)
            if not prod or not sigla:
                continue
            if r["fim"] is not None:
                ref = r["fim"]
            if r["municipio"]:
                mun.setdefault(f'{r["municipio"]}/{sigla}', {})[prod] = round(r["preco"], 2)
            else:
                uf.setdefault(sigla, {})[prod] = round(r["preco"], 2)
    if not uf and not mun:
        print("[aviso] planilha sem dados reconhecíveis; mantendo dados anteriores"); return 0
    if uf:
        g = [v["gasolina"] for v in uf.values() if "gasolina" in v]
        e = [v["etanol"] for v in uf.values() if "etanol" in v]
        atual["uf"] = uf
        if g: atual["nacional"] = {"gasolina": round(sum(g) / len(g), 2), "etanol": round(sum(e) / len(e), 2) if e else atual["nacional"].get("etanol")}
    if mun:
        atual["municipios"] = mun
    if isinstance(ref, (datetime.date, datetime.datetime)):
        atual["ref"] = ref.strftime("%Y-%m-%d")
    atual["fonte"] = "ANP, levantamento semanal de preços de revenda"
    atual["atualizado_em"] = datetime.date.today().isoformat()
    ARQ.write_text(json.dumps(atual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[ok] {len(uf)} estados e {len(mun)} municípios atualizados")
    return 0

if __name__ == "__main__":
    sys.exit(main())
