import os
import signal
import subprocess

def kill_processes():
    print("[SHUTDOWN] Killing backend (uvicorn)...")
    subprocess.call(["pkill", "-f", "uvicorn"])

    print("[SHUTDOWN] Killing frontend (npm run dev)...")
    subprocess.call(["pkill", "-f", "npm run dev"])

    print("[DONE] All processes stopped.")

if __name__ == "__main__":
    kill_processes()
