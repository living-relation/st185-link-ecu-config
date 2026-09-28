@echo off
rem Every harness gate, then the generated build list, buy list and min/ upload copies.
rem The old mutating steps (fix_cable_parts, layout_633) and the frozen-baseline
rem verify_rebuild were retired on 2026-09-27; see archive/2026-09-27-harness-redesign/.
cd /d %~dp0
python check_all.py || exit /b 1
