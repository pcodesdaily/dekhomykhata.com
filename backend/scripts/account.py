"""Create your MyKhata login, or reset its password. There is no sign-up page: this app has one owner.

Usage:
    python scripts/account.py you@example.com --name "Your Name"
"""

import argparse
import getpass

from mykhata_api.accounts import upsert_user
from mykhata_api.db import make_engine, session_factory
from mykhata_ml.config import load_config, path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("email")
    ap.add_argument("--name")
    args = ap.parse_args()

    password = getpass.getpass("New password: ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords don't match.")

    database = path(load_config()["api"]["database"])
    database.parent.mkdir(parents=True, exist_ok=True)
    with session_factory(make_engine(f"sqlite:///{database}"))() as db:
        try:
            user, created = upsert_user(db, args.email, password, args.name)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    print(f"{'Created' if created else 'Password reset for'} {user.email}. Log in at http://localhost:3000/login")


if __name__ == "__main__":
    main()
