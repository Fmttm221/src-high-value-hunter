.PHONY: compile smoke sync

compile:
python -m compileall -q src

smoke:
python tests/test_smoke.py

sync:
powershell -ExecutionPolicy Bypass -File scripts/sync-to-kali.ps1