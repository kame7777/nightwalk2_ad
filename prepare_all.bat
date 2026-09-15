@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === NightWalk PBF data preparation ===
python prepare_pbf_data.py --download
if errorlevel 1 goto :error
echo.
python prepare_graph.py --place "さいたま市, 埼玉, Japan"
if errorlevel 1 goto :error
echo.
echo === 完了 ===
echo 起動: streamlit run app.py
pause
exit /b 0
:error
echo エラーが発生しました。
pause
exit /b 1
