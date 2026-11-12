"""Assistente de Contas a Pagar com IA.

Exemplos:
  python -m src.main --modo local
  python -m src.main --modo ia --tempo-manual-por-nota 90
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

from . import extrator
from .alertas import gerar_alertas, resumo_em_texto
from .metricas import calcular_economia, comparar_com_gabarito, formatar_metricas
from .relatorio import salvar_csv, salvar_excel
from .validador import adicionar_colunas_de_prazo, validar_lancamentos

COLUNAS_EXTRACAO = ["fornecedor", "cnpj", "numero_documento", "valor", "vencimento", "categoria", "confianca", "observacoes"]


def processar_pasta(pasta: Path, modo: str) -> tuple[pd.DataFrame, float]:
    pdfs = sorted(pasta.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"Nenhum PDF encontrado em {pasta}. Rode antes: python -m src.gerar_notas_ficticias")

    cliente = extrator._criar_cliente() if modo == "ia" else None
    linhas, inicio = [], time.perf_counter()
    for i, pdf in enumerate(pdfs, start=1):
        print(f"[{i}/{len(pdfs)}] {pdf.name}")
        try:
            texto = extrator.ler_texto_pdf(pdf)
            dados = extrator.extrair_com_ia(pdf, cliente, texto) if modo == "ia" else extrator.extrair_local(texto)
        except Exception as erro:  # um documento com problema não pode derrubar o lote
            dados = {c: None for c in COLUNAS_EXTRACAO}
            dados.update(confianca=0.0, observacoes=f"Erro na extração: {erro}")
        linhas.append({"arquivo": pdf.name, **dados})
    return pd.DataFrame(linhas), time.perf_counter() - inicio


def main() -> None:
    p = argparse.ArgumentParser(description="Extrai, valida e organiza notas de Contas a Pagar.")
    p.add_argument("--modo", choices=["local", "ia"], default="local", help="local = regras offline; ia = Claude (precisa de chave)")
    p.add_argument("--pasta", default="data/notas_ficticias")
    p.add_argument("--saida", default="output")
    p.add_argument("--gabarito", default="data/gabarito.csv")
    p.add_argument("--data-referencia", default=date.today().isoformat(), help="AAAA-MM-DD (padrão: hoje)")
    p.add_argument("--dias-alerta", type=int, default=7)
    p.add_argument("--tempo-manual-por-nota", type=float, default=None, help="segundos que VOCÊ leva para lançar 1 nota à mão (meça!)")
    args = p.parse_args()

    data_ref = date.fromisoformat(args.data_referencia)
    saida = Path(args.saida)

    df, tempo_s = processar_pasta(Path(args.pasta), args.modo)
    df = validar_lancamentos(df)
    df = adicionar_colunas_de_prazo(df, data_ref)
    alertas = gerar_alertas(df, args.dias_alerta)

    salvar_excel(df, alertas, saida / "contas_a_pagar.xlsx", data_ref, args.dias_alerta)
    salvar_csv(df, saida / "lancamentos.csv")
    alertas.to_csv(saida / "alertas.csv", index=False, encoding="utf-8-sig")

    print("\n===== RESUMO =====")
    print(resumo_em_texto(df, alertas, args.dias_alerta))
    print(f"Tempo de extração ({args.modo}): {tempo_s:.1f} s para {len(df)} documentos")

    metricas = {"modo": args.modo, "tempo_extracao_s": round(tempo_s, 2)}
    if Path(args.gabarito).exists():
        m = comparar_com_gabarito(df, args.gabarito)
        metricas["qualidade"] = m
        print("\n===== QUALIDADE (comparação com o gabarito) =====")
        print(formatar_metricas(m))

    if args.tempo_manual_por_nota:
        if args.modo != "ia":
            print("\nObs.: a economia de tempo só faz sentido no modo ia (o modo local é um baseline).")
        else:
            e = calcular_economia(len(df), int((df["status"] == "REVISAR").sum()), tempo_s, args.tempo_manual_por_nota)
            metricas["economia"] = e
            print("\n===== ECONOMIA DE TEMPO (estimativa conservadora) =====")
            print(f"Manual:       {e['tempo_manual_total_s'] / 60:.1f} min")
            print(f"Automatizado: {e['tempo_automatizado_total_s'] / 60:.1f} min (extração + revisão das notas sinalizadas)")
            print(f"Economia:     {e['economia_pct']}%")
    else:
        print("\nDica: meça quanto tempo você leva para lançar 1 nota à mão e rode com --tempo-manual-por-nota SEGUNDOS.")

    (saida / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nArquivos gerados em: {saida}/ (contas_a_pagar.xlsx, lancamentos.csv, alertas.csv, metricas.json)")


if __name__ == "__main__":
    main()
