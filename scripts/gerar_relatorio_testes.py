#!/usr/bin/env python3
"""SBWAA — Relatório final de testes."""
import sys
import os

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from datetime import datetime
try:
    import chromadb
    col = chromadb.PersistentClient(path="knowledge/.chromadb").get_or_create_collection("sbwaa_knowledge")
    kb_count = col.count()
except Exception:
    kb_count = "N/A"

ROOT = Path(".")
VAULT = ROOT / "vault"
CACHE = ROOT / "scripts" / "data" / "cache"
hoje = datetime.now().strftime("%Y-%m-%d")

print(f"\n{'='*65}")
print(f"SBWAA — RELATÓRIO DE TESTES | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*65}")
print(f"\nScripts Python:    {len(list(ROOT.rglob('*.py')))} arquivos")
print(f"Cache de dados:    {len(list(CACHE.glob('*.json')))} arquivos")
print(f"Notas no vault:    {len(list(VAULT.rglob('*.md')))} arquivos")
print(f"DOCXs gerados:     {len(list(VAULT.rglob('*.docx')))} arquivos")
print(f"XLSXs gerados:     {len(list(VAULT.rglob('*.xlsx')))} arquivos")
print(f"Agentes (SKILL):   {len(list((ROOT/'.claude'/'agents').glob('*/SKILL.md')))}/8")
print(f"Scripts comandos:  {len(list((ROOT/'.claude'/'commands').glob('*.py')))}/14")
print(f"Knowledge base:    {kb_count} chunks indexados")
print(f"\n{'='*65}")
print("VERSÃO:")
print((ROOT / "VERSION.md").read_text(encoding="utf-8").strip())
print(f"{'='*65}\n")
