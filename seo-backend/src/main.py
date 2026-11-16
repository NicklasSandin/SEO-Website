"""Local development entry point: `python -m src.main` from the seo-backend folder.

Listens on 127.0.0.1 by default. The Flask debugger is off unless FLASK_DEBUG=1, and it refuses to
start with the debugger on a non-loopback address. For production use gunicorn (see the Dockerfile).
"""
import os

from .app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG") == "1"
    if debug and host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Refusing to run the Flask debugger on a non-loopback address.")
    app.run(host=host, port=int(os.environ.get("PORT", "5000")), debug=debug)
