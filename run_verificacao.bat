@echo off
cd /d F:\projects\server-app\server-app-tds-new
python verificar_leituras.py > verificacao_output.txt 2>&1
type verificacao_output.txt
echo.
echo Output salvo em: verificacao_output.txt
pause
