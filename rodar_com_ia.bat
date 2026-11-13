@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ==============================================
echo   Assistente de Contas a Pagar - rodar com IA
echo ==============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] O Python nao foi encontrado neste computador.
  echo Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
  echo Depois de instalar, de dois cliques neste arquivo de novo.
  pause
  exit /b 1
)

if not exist .venv (
  echo Preparando o ambiente pela primeira vez...
  python -m venv .venv
)
call .venv\Scripts\activate

echo Instalando as bibliotecas (pode levar 1 a 2 minutos)...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo [ERRO] Nao foi possivel instalar as bibliotecas. Verifique a internet e tente de novo.
  pause
  exit /b 1
)

echo.
if "%ANTHROPIC_API_KEY%"=="" (
  echo Cole sua chave da API e aperte Enter.
  echo ^(Para colar na janela preta: clique com o botao direito do mouse.^)
  set /p ANTHROPIC_API_KEY=Chave: 
)

echo.
set /p SEGUNDOS=Quantos segundos voce leva para lancar 1 nota a mao? (ex.: 84): 

echo.
echo Processando os documentos com IA. Pode levar alguns minutos...
echo.
python -m src.main --modo ia --tempo-manual-por-nota %SEGUNDOS%

echo.
echo ==============================================
echo  Pronto! Tire um print ou copie os numeros
echo  de "QUALIDADE" e "ECONOMIA DE TEMPO" acima.
echo  Os arquivos ficaram na pasta "output".
echo ==============================================
pause
