@echo off
rem Every harness gate, then the generated build list and buy list.
rem The old mutating steps (fix_cable_parts, layout_633) and the frozen-baseline
rem verify_rebuild were retired on 2026-09-27; see git history (the in-repo archive/ was removed 2026-10-13).
cd /d %~dp0
python check_all.py || exit /b 1
