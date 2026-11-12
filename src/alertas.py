"""Gera a lista de alertas: o que está vencido, o que vence logo e o que precisa de revisão."""
from __future__ import annotations

import pandas as pd

COLUNAS_ALERTA = ["tipo", "arquivo", "fornecedor", "valor", "vencimento", "detalhe"]
PRIORIDADE = {"VENCIDO": 0, "VENCE EM BREVE": 1, "REVISAR": 2}


def gerar_alertas(df: pd.DataFrame, dias_alerta: int = 7) -> pd.DataFrame:
    linhas = []
    for _, r in df.iterrows():
        d = r["dias_para_vencer"]
        if pd.notna(d):
            d = int(d)
            if d < 0:
                linhas.append(("VENCIDO", r, f"Venceu há {abs(d)} dia(s)"))
            elif d <= dias_alerta:
                linhas.append(("VENCE EM BREVE", r, "Vence hoje" if d == 0 else f"Vence em {d} dia(s)"))
        if r["status"] == "REVISAR":
            linhas.append(("REVISAR", r, r["motivos"]))

    alertas = pd.DataFrame(
        [
            {
                "tipo": tipo,
                "arquivo": r["arquivo"],
                "fornecedor": r["fornecedor"],
                "valor": r["valor"],
                "vencimento": r["vencimento"],
                "detalhe": detalhe,
            }
            for tipo, r, detalhe in linhas
        ],
        columns=COLUNAS_ALERTA,
    )
    if alertas.empty:
        return alertas
    alertas["_ordem"] = alertas["tipo"].map(PRIORIDADE)
    return alertas.sort_values(["_ordem", "vencimento"]).drop(columns="_ordem").reset_index(drop=True)


def resumo_em_texto(df: pd.DataFrame, alertas: pd.DataFrame, dias_alerta: int = 7) -> str:
    total = df["valor"].sum()
    vencidos = df.loc[df["dias_para_vencer"] < 0, "valor"].sum()
    em_breve = df.loc[(df["dias_para_vencer"] >= 0) & (df["dias_para_vencer"] <= dias_alerta), "valor"].sum()
    n_revisar = int((df["status"] == "REVISAR").sum())
    return (
        f"Documentos processados: {len(df)}\n"
        f"Total a pagar:          R$ {total:,.2f}\n"
        f"Vencidos:               R$ {vencidos:,.2f}\n"
        f"Vencem em até {dias_alerta} dias:   R$ {em_breve:,.2f}\n"
        f"Para revisão humana:    {n_revisar} documento(s)"
    )
