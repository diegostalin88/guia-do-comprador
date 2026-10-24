"""Atualiza data/taxas.json com a taxa média de juros de veículos (pessoa física) do Banco Central.

Fonte: SGS série 20749 (taxa média anual, % a.a.). Sem dependências externas.
Se a consulta falhar, mantém o arquivo como está e sai sem erro (o app usa o último valor).
"""
import json, sys, urllib.request, datetime, pathlib

SERIE = 20749
URL = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE}/dados/ultimos/1?formato=json"
ARQ = pathlib.Path(__file__).resolve().parent.parent / "data" / "taxas.json"

def main():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "guia-do-comprador/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dados = json.load(r)
        ultimo = dados[-1]
        anual = float(str(ultimo["valor"]).replace(",", "."))
        dia, mes, ano = ultimo["data"].split("/")
    except Exception as e:  # noqa: BLE001
        print(f"[aviso] Banco Central indisponível, mantendo valor anterior: {e}")
        return 0
    if not 5 < anual < 80:
        print(f"[aviso] valor fora do esperado ({anual}), ignorando")
        return 0
    mensal = ((1 + anual / 100) ** (1 / 12) - 1) * 100
    novo = {
        "ref": f"{ano}-{mes}",
        "fonte": "Banco Central, série SGS 20749 (taxa média de juros, aquisição de veículos, pessoa física)",
        "anual_pct": round(anual, 2),
        "mensal_pct": round(mensal, 2),
        "atualizado_em": datetime.date.today().isoformat(),
    }
    ARQ.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] taxa média {anual:.2f}% a.a. = {mensal:.2f}% a.m. (ref {ano}-{mes})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
