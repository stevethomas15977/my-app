import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.models import TenantRole
from app.repository import InMemoryTenantRepository
from app.services import (
    AuthorizationError,
    NotFoundError,
    TenantService,
    ValidationError,
)


repository = InMemoryTenantRepository()
tenant_service = TenantService(repository)


def get_header(headers: object, name: str, default: str) -> str:
    value = getattr(headers, "get")(name)
    return value if value else default


class TenantApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json({"status": "ok"})
                return

            if path == "/tenants":
                self._send_json(
                    {
                        "tenants": tenant_service.list_tenants_for_user(
                            self._cognito_sub(),
                            self._email(),
                        )
                    }
                )
                return

            tenant_id, collection = self._tenant_collection(path)
            if tenant_id and collection == "":
                self._send_json(
                    tenant_service.get_tenant_detail(
                        tenant_id,
                        self._cognito_sub(),
                        self._email(),
                    )
                )
                return
            if tenant_id and collection == "members":
                self._send_json(
                    {
                        "members": tenant_service.list_members(
                            tenant_id,
                            self._cognito_sub(),
                            self._email(),
                        )
                    }
                )
                return
            if tenant_id and collection == "invitations":
                self._send_json(
                    {
                        "invitations": tenant_service.list_invitations(
                            tenant_id,
                            self._cognito_sub(),
                            self._email(),
                        )
                    }
                )
                return

            raise NotFoundError("Route was not found")
        except Exception as error:
            self._send_error(error)

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            body = self._read_json()

            if path == "/tenants":
                self._send_json(
                    tenant_service.create_tenant(
                        tenant_name=body.get("tenant_name", ""),
                        admin_email=body.get("admin_email", self._email()),
                        actor_cognito_sub=self._cognito_sub(),
                        actor_display_name=body.get("display_name"),
                    ),
                    status=201,
                )
                return

            if path == "/invitations/accept":
                self._send_json(
                    tenant_service.accept_invitation(
                        token=body.get("token", ""),
                        cognito_sub=self._cognito_sub(),
                        email=self._email(),
                        display_name=body.get("display_name"),
                    )
                )
                return

            tenant_id, collection = self._tenant_collection(path)
            if tenant_id and collection == "invitations":
                role_value = body.get("role", TenantRole.TENANT_USER.value)
                self._send_json(
                    tenant_service.invite_user(
                        tenant_id=tenant_id,
                        invitee_email=body.get("email", ""),
                        role=TenantRole(role_value),
                        actor_cognito_sub=self._cognito_sub(),
                        actor_email=self._email(),
                    ),
                    status=201,
                )
                return

            raise NotFoundError("Route was not found")
        except Exception as error:
            self._send_error(error)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Cognito-Sub, X-User-Email")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, error: Exception) -> None:
        status = 500
        if isinstance(error, ValidationError):
            status = 400
        elif isinstance(error, AuthorizationError):
            status = 403
        elif isinstance(error, NotFoundError):
            status = 404
        elif isinstance(error, ValueError):
            status = 400

        self._send_json({"error": str(error)}, status=status)

    def _read_json(self) -> dict:
        content_length = int(get_header(self.headers, "Content-Length", "0"))
        if content_length == 0:
            return {}

        raw_body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_body)

    def _cognito_sub(self) -> str:
        return get_header(self.headers, "X-Cognito-Sub", "local-cognito-sub")

    def _email(self) -> str:
        return get_header(self.headers, "X-User-Email", "owner@example.com")

    def _tenant_collection(self, path: str) -> tuple[str | None, str | None]:
        parts = [part for part in path.split("/") if part]
        if len(parts) == 2 and parts[0] == "tenants":
            return parts[1], ""
        if len(parts) == 3 and parts[0] == "tenants":
            return parts[1], parts[2]
        return None, None


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), TenantApiHandler)
    print(f"Tenant API listening on http://{host}:{port}")
    server.serve_forever()
