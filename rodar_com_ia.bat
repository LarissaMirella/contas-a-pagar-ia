@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ==============================================
echo   Assistente de Contas a Pagar - rodar com IA
echo ==============================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto sem_python

if not exist .venv (
  echo Preparando o ambiente pela primeira vez...
  python -m venv .venv
)
call .venv\Scripts\activate

echo Instalando as bibliotecas (pode levar 1 a 2 minutos)...
python -m pip install -q -r requirements.txt
if errorlevel 1 goto sem_pip

rem Ignora configuracoes antigas de outras ferramentas que atrapalham a chave
set ANTHROPIC_AUTH_TOKEN=
set ANTHROPIC_BASE_URL=

:pedir_chave
echo.
echo Cole a sua chave da API e aperte Enter.
echo (Para colar na janela preta: clique com o botao direito do mouse.)
echo A chave de API comeca com sk-ant-
set "ANTHROPIC_API_KEY="
set /p ANTHROPIC_API_KEY=Chave: 
if not defined ANTHROPIC_API_KEY goto chave_invalida
set "ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY: =%"
echo %ANTHROPIC_API_KEY%| findstr /b /c:"sk-ant-" >nul
if errorlevel 1 goto chave_invalida
goto testar_chave

:chave_invalida
echo.
echo [ATENCAO] Isso nao parece uma chave da API. Ela deve comecar com sk-ant-
echo Crie uma em console.anthropic.com, no menu API Keys, e copie com o botao de copiar.
goto pedir_chave

:testar_chave
echo.
echo Testando a chave...
python -c "import os,anthropic; anthropic.Anthropic().messages.create(model=os.getenv('MODELO_CLAUDE','claude-sonnet-5-5'),max_tokens=5,messages=[{'role':'user','content':'oi'}]); print('Chave OK!')"
if errorlevel 1 goto teste_falhou

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
exit /b 0

:teste_falhou
echo.
echo [ERRO] O teste da chave falhou. Leia a mensagem acima e tire um print.
echo Nenhum documento foi processado e nada na pasta output foi alterado.
pause
exit /b 1

:sem_python
echo [ERRO] O Python nao foi encontrado neste computador.
echo Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
pause
exit /b 1

:sem_pip
echo [ERRO] Nao foi possivel instalar as bibliotecas. Verifique a internet e tente de novo.
pause
exit /b 1
