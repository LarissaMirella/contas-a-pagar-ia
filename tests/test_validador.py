import pandas as pd

from src.validador import cnpj_valido, formatar_cnpj, validar_lancamentos


def _linha(**extra):
    base = dict(
        arquivo="a.pdf", fornecedor="Fornecedor X", cnpj="11.222.333/0001-81",
        numero_documento="1", valor=100.0, vencimento="2026-11-20", categoria="Energia", confianca=0.95,
    )
    base.update(extra)
    return base


def test_cnpj_valido_e_invalido():
    assert cnpj_valido("11.222.333/0001-81")
    assert not cnpj_valido("11.222.333/0001-80")
    assert not cnpj_valido("00000000000000")
    assert not cnpj_valido("123")


def test_formatar_cnpj():
    assert formatar_cnpj("11222333000181") == "11.222.333/0001-81"


def test_documento_correto_fica_ok():
    df = validar_lancamentos(pd.DataFrame([_linha()]))
    assert df.loc[0, "status"] == "OK"


def test_detecta_duplicidade():
    df = validar_lancamentos(pd.DataFrame([_linha(arquivo="a.pdf"), _linha(arquivo="b.pdf")]))
    assert df.loc[0, "status"] == "OK"
    assert "duplicidade" in df.loc[1, "motivos"].lower()


def test_detecta_valor_muito_acima_do_padrao():
    linhas = [_linha(arquivo=f"{i}.pdf", numero_documento=str(i), valor=v) for i, v in enumerate([100, 110, 95, 2000])]
    df = validar_lancamentos(pd.DataFrame(linhas))
    assert df.loc[3, "status"] == "REVISAR"
    assert df.loc[0, "status"] == "OK"


def test_campo_ausente_e_confianca_baixa():
    df = validar_lancamentos(pd.DataFrame([_linha(valor=None, confianca=0.4)]))
    assert df.loc[0, "status"] == "REVISAR"
    assert "ausente" in df.loc[0, "motivos"].lower()
    assert "confiança baixa" in df.loc[0, "motivos"].lower()
