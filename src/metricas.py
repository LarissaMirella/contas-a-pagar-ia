"""Compara a extração com o gabarito e calcula acurácia e economia de tempo."""
from __future__ import annotations

import re

import pandas as pd

CAMPOS = ["fornecedor", "cnpj", "numero_documento", "valor", "vencimento", "categoria"]


def _texto(v) -> str:
    return "" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v).strip().lower()


def _iguais(campo: str, a, b) -> bool:
    if campo == "cnpj":
        return re.sub(r"\D", "", _texto(a)) == re.sub(r"\D", "", _texto(b))
    if campo == "valor":
        try:
            return abs(float(a) - float(b)) < 0.005
        except (TypeError, ValueError):
            return False
    if campo == "vencimento":
        da, db = pd.to_datetime(a, errors="coerce"), pd.to_datetime(b, errors="coerce")
        return pd.notna(da) and pd.notna(db) and da.date() == db.date()
    return _texto(a) == _texto(b)


def comparar_com_gabarito(df: pd.DataFrame, caminho_gabarito) -> dict:
    gab = pd.read_csv(caminho_gabarito, dtype=str)
    m = df.merge(gab, on="arquivo", suffixes=("", "_gab"))
    n = len(m)
    if n == 0:
        raise ValueError("Nenhum arquivo do gabarito foi encontrado nos resultados.")

    acertos = {c: 0 for c in CAMPOS}
    docs_com_erro = 0
    erros_sinalizados = 0
    for _, r in m.iterrows():
        erros = [c for c in CAMPOS if not _iguais(c, r[c], r[c + "_gab"])]
        for c in CAMPOS:
            acertos[c] += c not in erros
        if erros:
            docs_com_erro += 1
            erros_sinalizados += r["status"] == "REVISAR"

    total_campos = n * len(CAMPOS)
    return {
        "documentos": n,
        "acuracia_por_campo": {c: round(100 * acertos[c] / n, 1) for c in CAMPOS},
        "acuracia_geral": round(100 * sum(acertos.values()) / total_campos, 1),
        "documentos_totalmente_corretos": n - docs_com_erro,
        "documentos_com_algum_erro": docs_com_erro,
        "erros_sinalizados_para_revisao_pct": round(100 * erros_sinalizados / docs_com_erro, 1) if docs_com_erro else 100.0,
    }


def calcular_economia(n_docs: int, n_revisar: int, tempo_extracao_s: float, tempo_manual_por_nota_s: float) -> dict:
    """Estimativa conservadora: cada nota marcada para revisão leva o mesmo tempo que o lançamento manual."""
    manual = n_docs * tempo_manual_por_nota_s
    automatizado = tempo_extracao_s + n_revisar * tempo_manual_por_nota_s
    economia = manual - automatizado
    return {
        "tempo_manual_total_s": round(manual, 1),
        "tempo_automatizado_total_s": round(automatizado, 1),
        "economia_s": round(economia, 1),
        "economia_pct": round(100 * economia / manual, 1) if manual else 0.0,
    }


def formatar_metricas(m: dict) -> str:
    linhas = [f"Documentos comparados com o gabarito: {m['documentos']}", f"Acurácia geral (campos corretos): {m['acuracia_geral']}%", "Por campo:"]
    linhas += [f"  - {c}: {v}%" for c, v in m["acuracia_por_campo"].items()]
    linhas += [
        f"Documentos 100% corretos: {m['documentos_totalmente_corretos']} de {m['documentos']}",
        f"Documentos com algum erro que foram sinalizados para revisão: {m['erros_sinalizados_para_revisao_pct']}%",
    ]
    return "\n".join(linhas)
