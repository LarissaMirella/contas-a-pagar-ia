# Assistente de Contas a Pagar com IA

Automação que lê notas fiscais, faturas e boletos em PDF, extrai os dados com **Inteligência Artificial**, valida com regras de negócio e entrega uma planilha pronta para lançamento e para um **dashboard de fluxo de caixa no Power BI**.

> Projeto de portfólio criado por Larissa Mirella de Deus, a partir da rotina real de Contas a Pagar. **Todos os documentos, nomes, CNPJs e valores deste repositório são fictícios.**

## O problema

Lançar nota por nota (fornecedor, CNPJ, número, valor, vencimento, categoria) é lento, repetitivo e sujeito a erro de digitação. Um erro pode virar pagamento em duplicidade, multa por atraso ou previsão de caixa errada.

## A solução

```
PDFs (notas, faturas, boletos)
        |
        v
 [1] Extração com IA (Claude)  ---->  JSON: fornecedor, CNPJ, nº, valor, vencimento, categoria, confiança
        |
        v
 [2] Validação por regras      ---->  CNPJ válido? duplicada? valor fora do padrão? campo faltando? confiança baixa?
        |
        v
 [3] Alertas                   ---->  vencidos, vencem em até 7 dias, documentos para revisão humana
        |
        v
 [4] Excel + CSV               ---->  contas_a_pagar.xlsx  --->  [5] Dashboard no Power BI (fluxo de caixa)
```

**Decisão de projeto importante:** a IA não decide sozinha. Tudo o que for incerto ou suspeito recebe o status `REVISAR` e vai para uma pessoa conferir (*human-in-the-loop*). Em finanças, um erro silencioso custa mais caro do que o tempo economizado.

## Modos de execução

| Modo | O que faz | Precisa de chave de API? |
|---|---|---|
| `local` | Extração por regras simples (regex). É o **baseline** para comparar com a IA | Não |
| `ia` | Envia cada documento ao Claude e recebe os dados em JSON | Sim |

## Como rodar

Veja o passo a passo completo para iniciantes em [`docs/passo_a_passo_iniciante.md`](docs/passo_a_passo_iniciante.md). Resumo:

```bash
pip install -r requirements.txt
python -m src.gerar_notas_ficticias        # cria 31 PDFs fictícios + gabarito
python -m src.main --modo local            # roda sem chave de API
python -m src.main --modo ia --tempo-manual-por-nota 90   # roda com IA (precisa do .env)
python -m src.exemplo_resultado_ideal      # Excel "perfeito", para montar o Power BI antes da chave
```

## Dados de teste (31 documentos)

- 10 fornecedores fictícios, 3 layouts diferentes: **nota fiscal**, **boleto** e **fatura "solta"** (texto livre, com data por extenso e o número no meio da frase).
- Casos especiais de propósito: um **valor ~10x acima do padrão**, um **CNPJ inválido** e uma **nota enviada duas vezes**.
- `data/gabarito.csv` guarda as respostas corretas para medir a acurácia.

## Resultados

### Baseline por regras (modo `local`), medido de verdade

| Métrica | Resultado |
|---|---|
| Acurácia geral (campos corretos) | 87,1% |
| Documentos 100% corretos | 25 de 31 |
| Erros que foram sinalizados para revisão | 100% |
| Documentos enviados para revisão humana | 9 de 31 (6 por layout desconhecido, 1 CNPJ inválido, 1 valor atípico, 1 duplicada) |

As regras acertam os layouts que conhecem (nota e boleto) e falham em todas as faturas de texto livre. Esse é exatamente o limite de uma solução por regras: cada fornecedor novo exige código novo.

### IA (modo `ia`): preencha com os seus números

Rode `python -m src.main --modo ia --tempo-manual-por-nota SEGUNDOS` e copie o resultado:

| Métrica | Baseline (regras) | IA (Claude) |
|---|---|---|
| Acurácia geral | 87,1% | _preencher_ |
| Documentos 100% corretos | 25 de 31 | _preencher_ |
| Tempo para 31 documentos (manual) | _preencher_ | _preencher_ |
| Tempo com automação (extração + revisão) | - | _preencher_ |
| Economia de tempo | - | _preencher_ |

> **Como medir o tempo manual:** cronometre você mesma lançando 5 a 10 notas à mão numa planilha e divida pelo número de notas. Esse é o valor de `--tempo-manual-por-nota`.
> A estimativa de economia é **conservadora**: cada nota marcada como `REVISAR` conta como se levasse o mesmo tempo que o lançamento manual.

## Estrutura do projeto

```
src/
  gerar_notas_ficticias.py   cria os PDFs fictícios e o gabarito
  extrator.py                extração: modo IA (Claude) e modo local (regras)
  validador.py               regras de negócio (CNPJ, duplicidade, outlier, confiança)
  alertas.py                 vencidos, a vencer e revisão
  relatorio.py               gera Excel (com fórmulas no Resumo) e CSV
  metricas.py                acurácia vs gabarito e economia de tempo
  main.py                    orquestra tudo
  exemplo_resultado_ideal.py Excel com a extração perfeita (para treinar o Power BI)
tests/                       testes automatizados
docs/                        guia do Power BI, passo a passo, roteiro de apresentação
output/                      resultados gerados
```

## Dashboard no Power BI

Guia em [`docs/guia_power_bi.md`](docs/guia_power_bi.md): conexão com o Excel, medidas DAX e sugestão de visuais (total a pagar, vencidos, fluxo semanal, categorias, itens para revisão).

## Limitações e próximos passos

- Os documentos de teste são sintéticos; documentos reais têm mais ruído (escaneados, fotos, múltiplas páginas). O código já envia o PDF inteiro à IA quando não há texto extraível, mas isso precisa ser testado.
- A categoria é sugerida pela IA e deve ser conferida; um próximo passo é aprender com as correções feitas pela pessoa.
- Integração direta com o sistema financeiro (ERP) para eliminar o passo da planilha.
- Envio automático do resumo de vencimentos por e-mail.

## Privacidade

Nunca coloque documentos reais de empresas ou pessoas neste repositório. Ao usar uma API de IA com dados reais, confirme antes a política de dados da sua empresa e a LGPD. Não publique o arquivo `.env`.
