"""
GeoSmart AI -- Vercel Serverless Entrypoint (WSGI)
Course: Foundation Engineering and Design (21CEE301T)

Serves the interactive 3D Pile Foundation Simulator web application.
Exported variables: app, application, handler (satisfies Vercel Python runtime).
"""

import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML_PATH = os.path.join(CURRENT_DIR, "index.html")


def handler(environ, start_response):
    """WSGI entrypoint for Vercel Serverless runtime."""
    path = environ.get('PATH_INFO', '/')

    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "rb") as f:
            body = f.read()
        status = '200 OK'
        headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(body))),
            ('Cache-Control', 'public, max-age=0, must-revalidate')
        ]
    else:
        body = b"<!DOCTYPE html><html><body><h1>GeoSmart AI 3D Pile Foundation Simulator</h1></body></html>"
        status = '200 OK'
        headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(body)))
        ]

    start_response(status, headers)
    return [body]


# Top-level entrypoints required by Vercel
app = handler
application = handler


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = 8000
    print(f"Starting server on http://localhost:{port}")
    server = make_server('0.0.0.0', port, handler)
    server.serve_forever()
