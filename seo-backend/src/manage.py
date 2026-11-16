"""Small admin commands.

    python -m src.manage init-db
    python -m src.manage create-user you@example.com [--plan starter|professional|enterprise]
"""
import argparse
import getpass
import sys

from .app import create_app
from .config import PLANS
from .db_init import init_db
from .extensions import db
from .models import User
from .security import hash_password
from .validation import ValidationError, validate_email, validate_password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.manage")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="create missing tables and apply pending migrations")
    create = sub.add_parser("create-user", help="create an account (asks for the password)")
    create.add_argument("email")
    create.add_argument("--plan", choices=list(PLANS), default="starter")
    args = parser.parse_args(argv)

    app = create_app()
    with app.app_context():
        if args.command == "init-db":
            print(f"Database ready, schema version {init_db()}.")
            return 0
        try:
            email = validate_email(args.email)
            password = validate_password(getpass.getpass("Password: "))
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if User.query.filter_by(email=email).first():
            print("error: that email already has an account", file=sys.stderr)
            return 1
        db.session.add(User(email=email, password_hash=hash_password(password), plan=args.plan))
        db.session.commit()
        print(f"Created {email}.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
