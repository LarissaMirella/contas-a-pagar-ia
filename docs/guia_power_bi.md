# Guia: dashboard de fluxo de caixa no Power BI

Você pode montar o dashboard **antes** de ter a chave da API usando o arquivo
`output/exemplo_resultado_ideal/contas_a_pagar_ideal.xlsx`. Depois é só trocar a fonte para o `output/contas_a_pagar.xlsx` real.

## 1. Conectar os dados

1. Abra o **Power BI Desktop** (gratuito, só para Windows).
2. **Página Inicial > Obter dados > Pasta de trabalho do Excel**.
3. Escolha o arquivo e marque a aba **Lançamentos** (as outras abas são para leitura humana).
4. Clique em **Transformar dados** e confira os tipos de coluna:
   - `valor`: Número decimal fixo
   - `vencimento` e `semana_inicio`: Data
   - `dias_para_vencer`: Número inteiro
   - `confianca`: Número decimal
5. **Fechar e aplicar**.

## 2. Medidas (Modelagem > Nova medida)

```DAX
Total a Pagar = SUM('Lançamentos'[valor])

Vencidos (R$) =
CALCULATE([Total a Pagar], 'Lançamentos'[dias_para_vencer] < 0)

Vence em 7 dias (R$) =
CALCULATE(
    [Total a Pagar],
    'Lançamentos'[dias_para_vencer] >= 0,
    'Lançamentos'[dias_para_vencer] <= 7
)

Qtd a Revisar =
CALCULATE(COUNTROWS('Lançamentos'), 'Lançamentos'[status] = "REVISAR")

% a Revisar = DIVIDE([Qtd a Revisar], COUNTROWS('Lançamentos'))

Ticket Médio = AVERAGE('Lançamentos'[valor])
```

> A coluna `dias_para_vencer` é calculada na data de referência usada ao rodar o script.
> Para um painel "ao vivo", crie uma coluna calculada:
> `Dias para vencer (hoje) = DATEDIFF(TODAY(), 'Lançamentos'[vencimento], DAY)`
> e use-a nas medidas no lugar de `dias_para_vencer`.

## 3. Visuais sugeridos

| Visual | Campos |
|---|---|
| 4 Cartões no topo | Total a Pagar, Vencidos (R$), Vence em 7 dias (R$), Qtd a Revisar |
| Colunas: fluxo de caixa semanal | Eixo X: `semana_inicio` · Valores: Total a Pagar |
| Barras: por categoria | Eixo Y: `categoria` · Valores: Total a Pagar (ordene do maior para o menor) |
| Tabela "Para revisar" | `fornecedor`, `vencimento`, `valor`, `motivos` · filtro do visual: `status` = REVISAR |
| Segmentações | `categoria` e `status` |

## 4. Acabamento (faz diferença na apresentação)

- Título claro: "Contas a Pagar: previsão de caixa".
- Formate `valor` como moeda (R$) e `semana_inicio` como "dd/MM".
- Pinte o cartão "Vencidos" de vermelho e o de "a revisar" de amarelo.
- Tire um print e salve em `docs/img/dashboard.png` para colocar no README e no LinkedIn.
- Salve o `.pbix` na pasta do projeto (se for pequeno) ou publique um print/vídeo.
