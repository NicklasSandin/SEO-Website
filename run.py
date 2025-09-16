import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "seo-backend"
FRONTEND_DIR = BASE_DIR / "seo-service-website"
VENV_DIR = BACKEND_DIR / "venv"
REQ_FILE = BACKEND_DIR / "requirements.txt"


def run_cmd(cmd, cwd=None, check=True):
    print(f"[CMD] {' '.join(cmd)} (cwd={cwd})")
    return subprocess.run(cmd, cwd=cwd, check=check)


def ensure_system_deps():
    """Install system dependencies if missing"""
    print("[SETUP] Checking system dependencies...")

    needed = []
    for prog in ["python3", "npm", "xterm"]:
        if not shutil.which(prog):
            needed.append(prog)

    if needed:
        print(f"[INFO] Installing system packages: {', '.join(needed)}")
        try:
            run_cmd(["sudo", "apt-get", "update"])
            run_cmd(["sudo", "apt-get", "install", "-y"] + needed)
        except Exception as e:
            print(f"[WARN] Could not auto-install packages: {e}")


def ensure_venv():
    """Create or repair backend venv"""
    pip_exe = VENV_DIR / "bin" / "pip"

    if VENV_DIR.exists():
        try:
            run_cmd([str(pip_exe), "--version"])
            return
        except Exception as e:
            print(f"[WARN] venv broken: {e}, recreating...")
            shutil.rmtree(VENV_DIR, ignore_errors=True)

    print("[SETUP] Creating fresh venv...")
    run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])

    run_cmd([str(pip_exe), "install", "--upgrade", "pip"])

    if REQ_FILE.exists():
        run_cmd([str(pip_exe), "install", "-r", str(REQ_FILE)])
    else:
        print("[WARN] No requirements.txt found, skipping pip install.")


def ensure_frontend():
    """Install frontend dependencies"""
    print("[SETUP] Installing frontend dependencies...")
    run_cmd(["npm", "install", "--legacy-peer-deps"], cwd=FRONTEND_DIR)


def run_backend():
    """Run backend in background"""
    python_exe = VENV_DIR / "bin" / "python"
    backend_script = BACKEND_DIR / "seo_routes.py"

    if not backend_script.exists():
        backend_script.write_text('print("Dummy backend running...")')

    print("[RUN] Starting backend in background...")
    subprocess.Popen([str(python_exe), str(backend_script)],
                     cwd=BACKEND_DIR,
                     stdout=open("backend.log", "w"),
                     stderr=subprocess.STDOUT)


def run_frontend():
    """Run frontend in current terminal"""
    print("[RUN] Starting frontend with: npm run dev")
    subprocess.call(["npm", "run", "dev"], cwd=FRONTEND_DIR)


def run():
    ensure_system_deps()
    ensure_venv()
    ensure_frontend()
    run_backend()
    run_frontend()


if __name__ == "__main__":
    run()
