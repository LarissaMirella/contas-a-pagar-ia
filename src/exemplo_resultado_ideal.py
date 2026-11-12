"""Monta o Excel como ele ficaria se a extração acertasse tudo (usa o gabarito).

Serve para você construir o dashboard no Power BI ANTES de ter a chave da API,
e como "alvo" para comparar com o resultado real do modo ia.

Uso:  python -m src.exemplo_resultado_ideal [--data-referencia AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from .alertas import gerar_alertas
from .relatorio import salvar_excel
from .validador import adicionar_colunas_de_prazo, validar_lancamentos


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data-referencia", default=date.today().isoformat())
    p.add_argument("--saida", default="output/exemplo_resultado_ideal")
    args = p.parse_args()
    data_ref = date.fromisoformat(args.data_referencia)

    df = pd.read_csv("data/gabarito.csv", dtype={"numero_documento": str})
    df["confianca"] = 1.0
    df["observacoes"] = ""
    df = adicionar_colunas_de_prazo(validar_lancamentos(df), data_ref)
    alertas = gerar_alertas(df)
    saida = Path(args.saida)
    salvar_excel(df, alertas, saida / "contas_a_pagar_ideal.xlsx", data_ref)
    print(f"Gerado: {saida / 'contas_a_pagar_ideal.xlsx'}")


if __name__ == "__main__":
    main()
