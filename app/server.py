import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from app.database import connect, delete_item, get_item, init_db, list_items, upsert_item
from app.recommender import explain_item, recommend
from app.validation import validate_item


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token")
DB_PATH = os.getenv("DB_PATH")


def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Connection", "close")
    handler.end_headers()
    handler.wfile.write(body)
    handler.close_connection = True


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    @property
    def db_connection(self):
        if not hasattr(self.server, "db_connection"):
            self.server.db_connection = connect(DB_PATH) if DB_PATH else connect()
            init_db(self.server.db_connection)
        return self.server.db_connection

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def is_admin(self):
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {ADMIN_TOKEN}"

    def require_admin(self):
        if self.is_admin():
            return True
        json_response(self, 401, {"error": "Admin token required"})
        return False

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            json_response(
                self,
                200,
                {
                    "name": "Profile-to-Recommendation API",
                    "status": "running",
                    "endpoints": {
                        "health": "GET /health",
                        "recommend": "POST /recommend",
                        "admin_items": "GET /items with Authorization: Bearer dev-admin-token",
                        "explain": "GET /explain/{item_id}",
                    },
                },
            )
            return
        if path == "/health":
            json_response(self, 200, {"status": "ok"})
            return
        if path == "/items":
            if not self.require_admin():
                return
            json_response(self, 200, {"items": list_items(self.db_connection)})
            return
        if path.startswith("/explain/"):
            item_id = path.removeprefix("/explain/")
            item = get_item(self.db_connection, item_id)
            if not item:
                json_response(self, 404, {"error": "Item not found"})
                return
            json_response(self, 200, {"item_id": item_id, "logic": explain_item(item)})
            return
        json_response(self, 404, {"error": "Route not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        payload = self.read_json()
        if payload is None:
            json_response(self, 400, {"error": "Invalid JSON body"})
            return
        if path == "/recommend":
            items = list_items(self.db_connection, include_inactive=False)
            result = recommend(payload, items)
            json_response(self, 400 if result.get("errors") else 200, result)
            return
        if path == "/items":
            if not self.require_admin():
                return
            errors = validate_item(payload)
            if errors:
                json_response(self, 400, {"errors": errors})
                return
            json_response(self, 201, {"item": upsert_item(self.db_connection, payload)})
            return
        json_response(self, 404, {"error": "Route not found"})

    def do_PUT(self):
        path = urlparse(self.path).path
        if not path.startswith("/items/"):
            json_response(self, 404, {"error": "Route not found"})
            return
        if not self.require_admin():
            return
        item_id = path.removeprefix("/items/")
        payload = self.read_json()
        if payload is None:
            json_response(self, 400, {"error": "Invalid JSON body"})
            return
        payload["id"] = item_id
        errors = validate_item(payload)
        if errors:
            json_response(self, 400, {"errors": errors})
            return
        json_response(self, 200, {"item": upsert_item(self.db_connection, payload)})

    def do_DELETE(self):
        path = urlparse(self.path).path
        if not path.startswith("/items/"):
            json_response(self, 404, {"error": "Route not found"})
            return
        if not self.require_admin():
            return
        deleted = delete_item(self.db_connection, path.removeprefix("/items/"))
        json_response(self, 200 if deleted else 404, {"deleted": deleted})


def run(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(port=int(os.getenv("PORT", "8000")))