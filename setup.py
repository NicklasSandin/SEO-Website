import os
import sys
import zipfile
import shutil
import subprocess

BACKEND_ZIP = "seo-backend.zip"
FRONTEND_ZIP = "seo-service-website.zip"
BACKEND_DIR = "seo-backend"
FRONTEND_DIR = "seo-service-website"

def run_cmd(cmd, cwd=None):
    print(f">>> Running: {' '.join(cmd)} (in {cwd or os.getcwd()})")
    subprocess.check_call(cmd, cwd=cwd, shell=(sys.platform == "win32"))

def unzip_file(zip_path, extract_to, target_dir):
    if os.path.exists(target_dir):
        print(f"[CLEANUP] Removing old {target_dir}...")
        # kill anything using the backend venv before deletion
        if target_dir == BACKEND_DIR:
            subprocess.call(["pkill", "-f", f"{BACKEND_DIR}/venv/bin/python"])
        shutil.rmtree(target_dir, ignore_errors=True)
    print(f"=== Extracting {zip_path} ===")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def setup_backend():
    unzip_file(BACKEND_ZIP, ".", BACKEND_DIR)

    venv_path = os.path.join(BACKEND_DIR, "venv")
    pip_path = os.path.abspath(os.path.join(venv_path, "bin", "pip"))

    # Always recreate venv
    if os.path.exists(venv_path):
        print("[CLEANUP] Removing old venv...")
        shutil.rmtree(venv_path, ignore_errors=True)

    print("[SETUP] Creating new virtual environment...")
    run_cmd([sys.executable, "-m", "venv", venv_path])

    print("[SETUP] Upgrading pip...")
    run_cmd([pip_path, "install", "--upgrade", "pip"])

    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    if os.path.exists(req_file):
        print("[SETUP] Installing backend requirements...")
        run_cmd([pip_path, "install", "-r", req_file])
    else:
        print("[WARN] No requirements.txt found in backend.")


def setup_frontend():
    unzip_file(FRONTEND_ZIP, ".", FRONTEND_DIR)
    run_cmd(["npm", "install", "--legacy-peer-deps"], cwd=FRONTEND_DIR)

def main():
    setup_backend()
    setup_frontend()
    print("=== Setup Complete ===")
    print("To run backend: seo-backend/venv/bin/python seo_routes.py (Linux/macOS)")
    print("Or on Windows: seo-backend\\venv\\Scripts\\python.exe seo_routes.py")
    print("To run frontend: cd seo-service-website && npm run dev")

if __name__ == "__main__":
    main()
