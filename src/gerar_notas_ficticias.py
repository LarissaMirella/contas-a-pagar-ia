"""Gera notas fiscais, faturas e boletos FICTÍCIOS em PDF + o gabarito (respostas certas).

Todos os nomes, CNPJs e valores são inventados. Não use documentos reais de empresas
no portfólio (confidencialidade e LGPD).

Uso:  python -m src.gerar_notas_ficticias [--data-referencia AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .validador import calcular_digitos_cnpj, formatar_cnpj

PASTA_PDFS = Path("data/notas_ficticias")
GABARITO = Path("data/gabarito.csv")
CLIENTE = ("Empresa Exemplo Ltda", "11.222.333/0001-81")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# nome, base do CNPJ (8 dígitos), categoria, faixa de valor, descrições, layout (A=nota, B=boleto, C=fatura)
FORNECEDORES = [
    ("Distribuidora Horizonte Ltda", "23456789", "Matéria-prima", (8000, 24000), ["Matéria-prima: chapas de aço carbono", "Matéria-prima: barras de aço para produção"], "A"),
    ("Energia Vale Sul S.A.", "34567891", "Energia", (3000, 9000), ["Fornecimento de energia elétrica - consumo mensal"], "B"),
    ("TransLog Fretes Ltda", "45678912", "Frete e logística", (900, 4500), ["Serviço de frete rodoviário - transporte de carga"], "A"),
    ("Papelaria Central Eireli", "56789123", "Material de escritório", (150, 900), ["Material de escritório: papel, toner e canetas"], "A"),
    ("Nuvem Sistemas de TI Ltda", "67891234", "Serviços de TI", (1200, 3800), ["Licenças de software e suporte técnico"], "B"),
    ("Imobiliária Boa Vista Ltda", "78912345", "Aluguel", (6000, 6000), ["Aluguel do galpão - competência mensal"], "B"),
    ("ConectaFibra Telecom Ltda", "89123456", "Telecom", (400, 900), ["Internet e telefonia empresarial"], "C"),
    ("Mecânica Rápida Industrial Ltda", "91234567", "Manutenção", (700, 5200), ["Manutenção preventiva de empilhadeira"], "A"),
    ("Contabilidade Exata S/S", "12345670", "Serviços contábeis", (1800, 2200), ["Honorários de serviços contábeis"], "A"),
    ("Combustíveis Estrada Real Ltda", "13572468", "Combustível", (2000, 7000), ["Abastecimento de diesel da frota"], "C"),
]
DOCS_POR_FORNECEDOR = 3


def moeda_br(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def slug(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def cnpj_ficticio(base8: str) -> str:
    base12 = base8 + "0001"
    return formatar_cnpj(base12 + calcular_digitos_cnpj(base12))


def _linhas(c, linhas, x=50, y=700, passo=24):
    c.setFont("Helvetica", 12)
    for linha in linhas:
        c.drawString(x, y, linha)
        y -= passo


def desenhar_pdf(doc: dict, caminho: Path) -> None:
    c = canvas.Canvas(str(caminho), pagesize=A4)
    c.setTitle(f"Documento fictício {doc['numero_documento']}")
    layout = doc["layout"]
    valor = moeda_br(doc["valor"])
    venc = doc["vencimento"]
    if layout == "A":
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 780, "NOTA FISCAL ELETRÔNICA")
        _linhas(c, [
            f"Emitente: {doc['fornecedor']}",
            f"CNPJ: {doc['cnpj']}",
            f"Nº da Nota: {doc['numero_documento']}",
            f"Data de emissão: {data_br(doc['emissao'])}",
            f"Destinatário: {CLIENTE[0]} - CNPJ {CLIENTE[1]}",
            f"Descrição: {doc['descricao']}",
            f"Valor total: R$ {valor}",
            f"Vencimento: {data_br(venc)}",
        ])
    elif layout == "B":
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 780, "BOLETO DE COBRANÇA")
        _linhas(c, [
            f"Beneficiário: {doc['fornecedor']}",
            f"CNPJ do beneficiário: {doc['cnpj']}",
            f"Pagador: {CLIENTE[0]} - CNPJ {CLIENTE[1]}",
            f"Nº do documento: {doc['numero_documento']}",
            f"Referente a: {doc['descricao']}",
            f"Valor do documento: R$ {valor}",
            f"Data de vencimento: {data_br(venc)}",
            "Instruções: não receber após o vencimento.",
        ])
    else:  # layout C, mais "solto": a regra simples não consegue ler
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 780, "FATURA DE SERVIÇOS")
        _linhas(c, [
            f"Emitido por {doc['fornecedor']} (CNPJ {doc['cnpj']})",
            f"Fatura {doc['numero_documento']}",
            f"Referente a: {doc['descricao']}",
            f"Cliente: {CLIENTE[0]}",
            f"Total a pagar R$ {valor}",
            f"Vence em {venc.day} de {MESES[venc.month - 1]} de {venc.year}",
        ])
    c.save()


def gerar(data_ref: date) -> int:
    rng = random.Random(42)
    PASTA_PDFS.mkdir(parents=True, exist_ok=True)
    for antigo in PASTA_PDFS.glob("*.pdf"):
        antigo.unlink()

    docs: list[dict] = []
    for nome, base, categoria, (lo, hi), descricoes, layout in FORNECEDORES:
        cnpj = cnpj_ficticio(base)
        numeros: set[int] = set()
        for _ in range(DOCS_POR_FORNECEDOR):
            n = rng.randint(100, 9999)
            while n in numeros:
                n = rng.randint(100, 9999)
            numeros.add(n)
            venc = data_ref + timedelta(days=rng.randint(-12, 35))
            numero = f"{data_ref.year}/{n:04d}" if layout == "C" else f"{n:06d}"
            docs.append({
                "fornecedor": nome, "cnpj": cnpj, "numero_documento": numero,
                "valor": round(rng.uniform(lo, hi), 2), "vencimento": venc,
                "emissao": venc - timedelta(days=rng.randint(20, 40)),
                "categoria": categoria, "descricao": rng.choice(descricoes), "layout": layout,
            })

    # Casos especiais para testar as validações
    primeiro_frete = next(d for d in docs if d["categoria"] == "Frete e logística")
    primeiro_frete["valor"] = 31250.00  # valor muito acima do padrão
    primeira_papelaria = next(d for d in docs if d["categoria"] == "Material de escritório")
    primeira_papelaria["cnpj"] = primeira_papelaria["cnpj"][:-1] + ("0" if primeira_papelaria["cnpj"][-1] != "0" else "1")  # CNPJ inválido
    original_ti = next(d for d in docs if d["categoria"] == "Serviços de TI")
    duplicata = dict(original_ti, copia=True)  # mesma nota enviada duas vezes
    docs.append(duplicata)

    linhas_gabarito = []
    for i, d in enumerate(docs, start=1):
        sufixo = "_reenviada" if d.get("copia") else ""
        arquivo = f"{i:02d}_{slug(d['fornecedor'])}_{slug(d['numero_documento'])}{sufixo}.pdf"
        desenhar_pdf(d, PASTA_PDFS / arquivo)
        linhas_gabarito.append({
            "arquivo": arquivo, "fornecedor": d["fornecedor"], "cnpj": d["cnpj"],
            "numero_documento": d["numero_documento"], "valor": f"{d['valor']:.2f}",
            "vencimento": d["vencimento"].isoformat(), "categoria": d["categoria"],
        })

    with open(GABARITO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_gabarito[0].keys()))
        w.writeheader()
        w.writerows(linhas_gabarito)
    return len(docs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera documentos fictícios para o projeto.")
    parser.add_argument("--data-referencia", default=date.today().isoformat(), help="AAAA-MM-DD (padrão: hoje)")
    args = parser.parse_args()
    total = gerar(date.fromisoformat(args.data_referencia))
    print(f"{total} documentos fictícios criados em {PASTA_PDFS} e gabarito em {GABARITO}")
