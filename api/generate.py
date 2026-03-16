
import io
import qrcode
import qrcode.constants
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


MAX_LENGTH = 2048


class handler(BaseHTTPRequestHandler):
    """Vercel calls this class for every request."""

    def do_GET(self):
        
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        text = params.get("text", [""])[0].strip()
        size = params.get("size", ["200"])[0]

        
        cors = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
        }

        
        if not text:
            self._send_json(400, {"error": "text param is required"}, cors)
            return

        if len(text) > MAX_LENGTH:
            self._send_json(400, {"error": f"Max {MAX_LENGTH} characters"}, cors)
            return

        try:
            px = max(100, min(400, int(size)))
        except ValueError:
            px = 200

        # ── Generate QR ─────────────────────────────────────────────────
        try:
            qr = qrcode.QRCode(
                version=None,                          
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # resize to requested px
            img = img.resize((px, px))

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            png_bytes = buf.getvalue()

        except Exception as e:
            self._send_json(500, {"error": str(e)}, cors)
            return

        # ── Send PNG response ────────────────────────────────────────────
        self.send_response(200)
        for k, v in cors.items():
            self.send_header(k, v)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(png_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(png_bytes)

    def do_OPTIONS(self):
        """Preflight CORS."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def _send_json(self, status, body, extra_headers=None):
        import json
        data = json.dumps(body).encode()
        self.send_response(status)
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # silence default request logs in Vercel
    def log_message(self, format, *args):
        pass
