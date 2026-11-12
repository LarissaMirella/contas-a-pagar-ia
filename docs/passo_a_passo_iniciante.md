# Passo a passo para quem nunca criou um projeto

## 1. Preparar o computador (uma vez só)

1. Instale o **Python 3.10 ou mais novo**: https://www.python.org/downloads/
   No Windows, na primeira tela do instalador, marque **"Add Python to PATH"**.
2. Instale o **VS Code**: https://code.visualstudio.com/
3. Instale o **Git**: https://git-scm.com/downloads
4. Crie uma conta gratuita no **GitHub**: https://github.com

## 2. Abrir o projeto

1. Descompacte a pasta `contas-a-pagar-ia`.
2. No VS Code: **Arquivo > Abrir Pasta** e escolha `contas-a-pagar-ia`.
3. Abra o terminal: **Terminal > Novo Terminal**.

## 3. Criar o ambiente e instalar as bibliotecas

Windows (PowerShell):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Mac/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
O "venv" é uma caixa isolada para as bibliotecas deste projeto. Você verá `(.venv)` no começo da linha do terminal.

## 4. Rodar sem IA (para ver tudo funcionando)

```
python -m src.gerar_notas_ficticias
python -m src.main --modo local
```
Abra `output/contas_a_pagar.xlsx` e confira as abas Resumo, Lançamentos e Alertas.

## 5. Rodar com IA

1. Crie uma conta e uma chave de API em https://console.anthropic.com (a API é cobrada por uso e é separada da assinatura do Claude no site; confira o preço atual no console).
2. Copie o arquivo `.env.example` e renomeie a cópia para `.env`.
3. Abra o `.env` e troque `cole_sua_chave_aqui` pela sua chave.
4. Rode:
```
python -m src.main --modo ia
```
5. Quando medir o tempo manual (cronometre você lançando 5 a 10 notas à mão):
```
python -m src.main --modo ia --tempo-manual-por-nota 90
```
(troque 90 pelos seus segundos por nota).

**Importante:** o modo `ia` foi escrito e revisado, mas não pôde ser executado com uma chave real durante a criação do projeto. Se aparecer algum erro, copie a mensagem e peça ajuda: é normal precisar de um ajuste na primeira execução real.

## 6. Publicar no GitHub

1. No GitHub: **New repository**, nome `contas-a-pagar-ia`, deixe **público**, não marque "Add README".
2. No terminal do VS Code:
```
git init
git add .
git commit -m "Primeira versão do assistente de Contas a Pagar com IA"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/contas-a-pagar-ia.git
git push -u origin main
```
3. Confira se o arquivo `.env` **não** apareceu no GitHub (ele já está no `.gitignore`). Se a chave vazar, apague-a no console e crie outra.

## 7. Rodar os testes automáticos

```
python -m pytest
```
Tudo verde significa que as validações continuam funcionando depois de qualquer mudança que você fizer.
