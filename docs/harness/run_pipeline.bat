@echo off
cd /d %~dp0
echo === fix_cable_parts ===
python fix_cable_parts.py || exit /b 1
echo.
echo === layout_633 ===
python layout_633.py || exit /b 1
echo.
echo === lint_v09 ===
python lint_v09.py || exit /b 1
echo.
echo === verify_rebuild ===
python verify_rebuild.py || exit /b 1
echo.
echo === make_min ===
python make_min.py || exit /b 1
