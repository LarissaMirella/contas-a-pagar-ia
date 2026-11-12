"""Validações de negócio para os lançamentos extraídos.

A IA lê o documento, mas quem garante a qualidade é este módulo: ele aplica
regras simples e transparentes (CNPJ, duplicidade, valor fora do padrão,
confiança baixa) e marca com o status "REVISAR" o que precisa de olhar humano.
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

CAMPOS_OBRIGATORIOS = ["fornecedor", "cnpj", "numero_documento", "valor", "vencimento"]

PESOS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def so_digitos(texto) -> str:
    """Remove tudo que não é número ('12.345/0001-95' -> '123450001...')."""
    return re.sub(r"\D", "", str(texto if texto is not None else ""))


def _digito(base: str, pesos: list[int]) -> int:
    soma = sum(int(d) * p for d, p in zip(base, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def calcular_digitos_cnpj(base12: str) -> str:
    """Calcula os 2 dígitos verificadores a partir dos 12 primeiros dígitos."""
    d1 = _digito(base12, PESOS_1)
    d2 = _digito(base12 + str(d1), PESOS_2)
    return f"{d1}{d2}"


def cnpj_valido(cnpj) -> bool:
    n = so_digitos(cnpj)
    if len(n) != 14 or len(set(n)) == 1:
        return False
    return n[12:] == calcular_digitos_cnpj(n[:12])


def formatar_cnpj(cnpj) -> str:
    n = so_digitos(cnpj)
    if len(n) != 14:
        return str(cnpj) if cnpj else ""
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"


def _vazio(valor) -> bool:
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        pass
    return str(valor).strip() == ""


def validar_lancamentos(
    df: pd.DataFrame,
    limiar_confianca: float = 0.8,
    fator_outlier: float = 3.0,
    min_docs_categoria: int = 3,
) -> pd.DataFrame:
    """Devolve o DataFrame com as colunas 'status' (OK/REVISAR) e 'motivos'."""
    df = df.copy().reset_index(drop=True)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["vencimento"] = pd.to_datetime(df["vencimento"], errors="coerce")
    df["confianca"] = pd.to_numeric(df["confianca"], errors="coerce").fillna(0.0)
    df["categoria"] = df["categoria"].where(~df["categoria"].map(_vazio), "Outros")

    cnpj_num = df["cnpj"].map(so_digitos)
    numero = df["numero_documento"].map(lambda v: "" if _vazio(v) else str(v).strip())
    chave = cnpj_num + "|" + numero
    duplicado = chave.duplicated(keep="first") & (numero != "") & (cnpj_num != "")

    mediana_cat = df.groupby("categoria")["valor"].transform("median")
    qtd_cat = df.groupby("categoria")["valor"].transform("count")

    todos_motivos: list[str] = []
    for i in range(len(df)):
        m: list[str] = []
        ausentes = [c for c in CAMPOS_OBRIGATORIOS if _vazio(df.at[i, c])]
        if ausentes:
            m.append("Campo(s) ausente(s): " + ", ".join(ausentes))
        if not _vazio(df.at[i, "cnpj"]) and not cnpj_valido(df.at[i, "cnpj"]):
            m.append("CNPJ inválido")
        if pd.notna(df.at[i, "valor"]) and df.at[i, "valor"] <= 0:
            m.append("Valor menor ou igual a zero")
        if duplicado.iat[i]:
            m.append("Possível duplicidade (mesmo CNPJ e número de documento)")
        if (
            pd.notna(df.at[i, "valor"])
            and qtd_cat.iat[i] >= min_docs_categoria
            and mediana_cat.iat[i] > 0
            and df.at[i, "valor"] > fator_outlier * mediana_cat.iat[i]
        ):
            m.append(f"Valor muito acima do padrão da categoria (mediana R$ {mediana_cat.iat[i]:,.2f})")
        if df.at[i, "confianca"] < limiar_confianca:
            m.append(f"Confiança baixa ({df.at[i, 'confianca']:.2f})")
        todos_motivos.append("; ".join(m))

    df["motivos"] = todos_motivos
    df["status"] = df["motivos"].map(lambda t: "REVISAR" if t else "OK")
    return df


def adicionar_colunas_de_prazo(df: pd.DataFrame, data_ref: date) -> pd.DataFrame:
    """Cria 'dias_para_vencer' e 'semana_inicio' (segunda-feira da semana do vencimento)."""
    df = df.copy()
    venc = pd.to_datetime(df["vencimento"], errors="coerce")
    ref = pd.Timestamp(data_ref)
    df["dias_para_vencer"] = (venc - ref).dt.days
    df["semana_inicio"] = venc - pd.to_timedelta(venc.dt.weekday, unit="D")
    return df
