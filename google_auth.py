import json
import os
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


class GoogleOAuthFlow:
    def __init__(self, controller):
        self.controller = controller
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8765/callback").strip()
        self.state = None

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def start_login(self):
        if not self.is_configured():
            self.controller.show_login_message(
                "Google sign-in is not configured yet. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )
            return

        self.state = os.urandom(16).hex()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": self.state,
        }

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        webbrowser.open(auth_url)

        threading.Thread(target=self._run_callback_server, daemon=True).start()

    def _run_callback_server(self):
        port = 8765
        handler = self._build_handler()

        try:
            server = HTTPServer(("127.0.0.1", port), handler)
        except OSError:
            self.controller.show_login_message(
                "Port 8765 is busy. Please close any other local callback server and try again."
            )
            return

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()

    def _build_handler(self):
        outer_self = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path != "/callback":
                    self.send_response(404)
                    self.end_headers()
                    return

                query = urllib.parse.parse_qs(parsed.query)
                code = query.get("code", [""])[0]
                state = query.get("state", [""])[0]

                if state != outer_self.state:
                    outer_self.controller.show_login_message("Google login failed: state mismatch.")
                    self._send_success_page("Login failed because the request could not be verified.")
                    return

                if not code:
                    outer_self.controller.show_login_message("Google login was cancelled.")
                    self._send_success_page("Login cancelled.")
                    return

                try:
                    user_info = outer_self._exchange_code(code)
                    outer_self.controller.complete_google_login(user_info)
                    self._send_success_page("Login completed. You can close this window.")
                except Exception as exc:
                    outer_self.controller.show_login_message(f"Google login failed: {exc}")
                    self._send_success_page("Login failed. Please try again.")

                self.server.shutdown()

            def log_message(self, _format, *args):
                return

            def _send_success_page(self, message):
                html = f"""
                <html>
                    <body style='font-family: Arial; padding: 24px;'>
                        <h3>{message}</h3>
                        <p>You can close this tab and return to the app.</p>
                    </body>
                </html>
                """
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return CallbackHandler

    def _exchange_code(self, code):
        data = urllib.parse.urlencode(
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            token_data = json.load(response)

        access_token = token_data.get("access_token")
        if not access_token:
            raise RuntimeError("Google did not return an access token.")

        user_info_request = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        with urllib.request.urlopen(user_info_request) as response:
            return json.load(response)
