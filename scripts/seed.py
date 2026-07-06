import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import connect, init_db, upsert_item
from seed_data import ITEMS


def main():
    connection = connect()
    init_db(connection)
    for item in ITEMS:
        upsert_item(connection, item)
    print(f"Seeded {len(ITEMS)} catalogue items.")


if __name__ == "__main__":
    main()
