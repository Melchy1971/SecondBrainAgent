
import subprocess, sys, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run_cmd(args):
    return subprocess.run([sys.executable, str(ROOT/'launcher.py'), '--project-root', str(ROOT), *args], cwd=ROOT, text=True, capture_output=True, timeout=20)


def test_improve_cli_smoke():
    r=run_cmd(['improve-status'])
    assert r.returncode == 0, r.stderr + r.stdout
    assert 'feedback_count' in r.stdout


def test_improve_feedback_cli_smoke():
    r=run_cmd(['improve-feedback','user','command','launcher','-1','--text','docs unclear'])
    assert r.returncode == 0, r.stderr + r.stdout
    b=run_cmd(['improve-backlog'])
    assert b.returncode == 0
    assert 'docs unclear' in b.stdout
