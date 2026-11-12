"""Salva os resultados em Excel (para leitura humana e Power BI) e CSV."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

FONTE = "Arial"
COLUNAS = [
    "arquivo", "fornecedor", "cnpj", "numero_documento", "valor", "vencimento", "categoria",
    "confianca", "status", "motivos", "dias_para_vencer", "semana_inicio", "observacoes",
]
FORMATOS = {"valor": 'R$ #,##0.00', "vencimento": "dd/mm/yyyy", "semana_inicio": "dd/mm/yyyy", "confianca": "0.00"}


def _para_python(v):
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, pd.Timestamp):
        return v.date()
    if hasattr(v, "item"):
        return v.item()
    return v


def _cabecalho(ws, linha: int, titulos: list[str]):
    for j, t in enumerate(titulos, start=1):
        c = ws.cell(row=linha, column=j, value=t)
        c.font = Font(name=FONTE, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", start_color="1F4E78")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _largura(ws, larguras: dict[str, float]):
    for letra, w in larguras.items():
        ws.column_dimensions[letra].width = w


def _fonte_padrao(ws):
    for linha in ws.iter_rows():
        for c in linha:
            if c.font is None or c.font.name != FONTE:
                c.font = Font(name=FONTE, bold=c.font.bold if c.font else False, color=c.font.color if c.font else None, size=10)


def salvar_excel(df: pd.DataFrame, alertas: pd.DataFrame, caminho: Path, data_ref: date, dias_alerta: int = 7) -> None:
    wb = Workbook()

    # --- Lançamentos (valores, sem fórmulas: é a fonte de dados do Power BI)
    ws = wb.active
    ws.title = "Lançamentos"
    _cabecalho(ws, 1, COLUNAS)
    for i, (_, r) in enumerate(df.iterrows(), start=2):
        for j, col in enumerate(COLUNAS, start=1):
            c = ws.cell(row=i, column=j, value=_para_python(r.get(col)))
            c.font = Font(name=FONTE, size=10)
            if col in FORMATOS:
                c.number_format = FORMATOS[col]
        if r["status"] == "REVISAR":
            ws.cell(row=i, column=COLUNAS.index("status") + 1).fill = PatternFill("solid", start_color="FFD966")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS))}{len(df) + 1}"
    _largura(ws, {"A": 46, "B": 32, "C": 20, "D": 16, "E": 14, "F": 12, "G": 22, "H": 10, "I": 10, "J": 60, "K": 12, "L": 12, "M": 34})

    # --- Alertas
    wa = wb.create_sheet("Alertas")
    _cabecalho(wa, 1, ["tipo", "arquivo", "fornecedor", "valor", "vencimento", "detalhe"])
    for i, (_, r) in enumerate(alertas.iterrows(), start=2):
        for j, col in enumerate(["tipo", "arquivo", "fornecedor", "valor", "vencimento", "detalhe"], start=1):
            c = wa.cell(row=i, column=j, value=_para_python(r[col]))
            c.font = Font(name=FONTE, size=10)
            if col in FORMATOS:
                c.number_format = FORMATOS[col]
    wa.freeze_panes = "A2"
    _largura(wa, {"A": 16, "B": 46, "C": 32, "D": 14, "E": 12, "F": 80})

    # --- Resumo (fórmulas sobre a aba Lançamentos)
    wr = wb.create_sheet("Resumo", 0)
    n = len(df) + 1
    L = {c: get_column_letter(COLUNAS.index(c) + 1) for c in COLUNAS}

    def rng(col):
        return f"'Lançamentos'!${L[col]}$2:${L[col]}${n}"

    wr["A1"] = "Resumo de Contas a Pagar"
    wr["A1"].font = Font(name=FONTE, bold=True, size=14)
    wr["A2"] = "Os valores abaixo são fórmulas calculadas a partir da aba Lançamentos."
    wr["A2"].font = Font(name=FONTE, italic=True, size=9, color="595959")
    wr["A3"], wr["B3"] = "Data de referência", data_ref
    wr["B3"].number_format = "dd/mm/yyyy"
    wr["A4"], wr["B4"] = "Janela de alerta (dias)", dias_alerta
    indicadores = [
        ("Total a pagar", f"=SUM({rng('valor')})", "R$ #,##0.00"),
        ("Vencidos (R$)", f'=SUMIFS({rng("valor")},{rng("dias_para_vencer")},"<0")', "R$ #,##0.00"),
        ("Vencem na janela de alerta (R$)", f'=SUMIFS({rng("valor")},{rng("dias_para_vencer")},">=0",{rng("dias_para_vencer")},"<="&$B$4)', "R$ #,##0.00"),
        ("Lançamentos para revisar", f'=COUNTIF({rng("status")},"REVISAR")', "0"),
        ("Total de lançamentos", f"=COUNTA({rng('arquivo')})", "0"),
    ]
    for k, (rotulo, formula, fmt) in enumerate(indicadores, start=6):
        wr.cell(row=k, column=1, value=rotulo)
        c = wr.cell(row=k, column=2, value=formula)
        c.number_format = fmt

    linha = 13
    wr.cell(row=linha, column=1, value="Por categoria")
    _cabecalho(wr, linha + 1, ["Categoria", "Total (R$)", "Qtd"])
    categorias = df.groupby("categoria")["valor"].sum().sort_values(ascending=False).index.tolist()
    for k, cat in enumerate(categorias, start=linha + 2):
        wr.cell(row=k, column=1, value=cat)
        wr.cell(row=k, column=2, value=f'=SUMIFS({rng("valor")},{rng("categoria")},$A{k})').number_format = "R$ #,##0.00"
        wr.cell(row=k, column=3, value=f'=COUNTIF({rng("categoria")},$A{k})')
    linha = linha + 2 + len(categorias) + 1

    wr.cell(row=linha, column=1, value="Fluxo de caixa previsto por semana (início na segunda-feira)")
    _cabecalho(wr, linha + 1, ["Semana de", "Total (R$)", "Qtd"])
    semanas = pd.to_datetime(df["semana_inicio"]).dropna()
    if not semanas.empty:
        todas = pd.date_range(semanas.min(), semanas.max(), freq="7D")
        for k, s in enumerate(todas, start=linha + 2):
            c = wr.cell(row=k, column=1, value=s.date())
            c.number_format = "dd/mm/yyyy"
            wr.cell(row=k, column=2, value=f'=SUMIFS({rng("valor")},{rng("semana_inicio")},$A{k})').number_format = "R$ #,##0.00"
            wr.cell(row=k, column=3, value=f'=COUNTIF({rng("semana_inicio")},$A{k})')
    _largura(wr, {"A": 52, "B": 18, "C": 8})

    for aba in (wr,):
        for linha_cells in aba.iter_rows():
            for c in linha_cells:
                if c.value is not None and not (c.font and c.font.bold and c.font.color and c.font.color.rgb == "00FFFFFF"):
                    if c.font.name != FONTE:
                        c.font = Font(name=FONTE, bold=c.font.bold, italic=c.font.italic, size=c.font.size if c.font.size != 11 else 10, color=c.font.color)
    for rotulo_linha in (13,):
        wr.cell(row=rotulo_linha, column=1).font = Font(name=FONTE, bold=True)
    wr.cell(row=linha, column=1).font = Font(name=FONTE, bold=True)

    caminho.parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho)


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df[[c for c in COLUNAS if c in df.columns]].to_csv(caminho, index=False, encoding="utf-8-sig")
