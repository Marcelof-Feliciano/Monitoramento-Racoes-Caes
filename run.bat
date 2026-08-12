@echo off
REM Executa o coletor e guarda a saida em logs\run.log
REM %~dp0 = a pasta onde este .bat esta (nao precisa editar caminho)
cd /d "%~dp0"
if not exist logs mkdir logs
echo ============================================== >> logs\run.log
echo Execucao: %date% %time% >> logs\run.log
python main.py >> logs\run.log 2>&1
