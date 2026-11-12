from src.extrator import br_para_float, data_br_para_iso, extrair_local, _limpar_json

NOTA = """NOTA FISCAL ELETRÔNICA
Emitente: Fornecedor Teste Ltda
CNPJ: 11.222.333/0001-81
Nº da Nota: 000123
Destinatário: Empresa Exemplo Ltda - CNPJ 55.666.777/0001-00
Descrição: Aluguel do galpão
Valor total: R$ 1.234,56
Vencimento: 25/11/2026"""


def test_conversores():
    assert br_para_float("1.234,56") == 1234.56
    assert data_br_para_iso("25/11/2026") == "2026-11-25"


def test_extrair_local_layout_nota():
    d = extrair_local(NOTA)
    assert d["fornecedor"] == "Fornecedor Teste Ltda"
    assert d["cnpj"] == "11.222.333/0001-81"  # pega o CNPJ do emitente, não o do destinatário
    assert d["numero_documento"] == "000123"
    assert d["valor"] == 1234.56
    assert d["vencimento"] == "2026-11-25"
    assert d["categoria"] == "Aluguel"
    assert d["confianca"] == 1.0


def test_extrair_local_layout_desconhecido_tem_confianca_baixa():
    d = extrair_local("FATURA\nTotal a pagar R$ 10,00\nVence em 3 de dezembro de 2026")
    assert d["confianca"] < 0.5


def test_limpar_json_aceita_markdown():
    assert _limpar_json('```json\n{"valor": 1}\n```') == {"valor": 1}
