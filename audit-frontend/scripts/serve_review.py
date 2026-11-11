#!/usr/bin/env python3
"""Serve one review on loopback, with an explicit allow-list for companion assets.

    python3 serve_review.py /path/to/review.html [--port 8765]
    python3 serve_review.py /path/to/review.html --allow-asset screenshots --allow-asset coverage.html

Assets are relative to the report's directory (absolute paths within it also work).
Directories allow only image/font/style/HTML files, never notes, auth state, helper
scripts or directory listings. Feedback pages may explicitly allow review-input.js;
no other scripts are served. The embedded-picture report needs no allowed assets.
The printed localhost URL is usable from the host browser, including WSL forwarding.
Leave this process running until the owner is done; Ctrl-C stops it. Browser rulings
are origin-local: reuse the printed port with --port and the same storage_key when
returning to the review. A new port has separate browser storage.
"""
import argparse
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ASSET_TYPES = {'.html', '.htm', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg',
               '.avif', '.ico', '.css', '.woff', '.woff2', '.ttf', '.otf'}
PRIVATE_DIRS = {'notes', 'auth', 'auth-state', 'browser-state', 'storage-state',
                'scripts', 'helpers', 'node_modules'}


def public_asset(relative):
    return (relative.suffix.lower() in ASSET_TYPES
            and all(not part.startswith('.') and part.lower() not in PRIVATE_DIRS
                    for part in relative.parts))


def make_handler(report, assets):
    root = report.parent
    files = {report}
    directories = []
    for asset in assets:
        candidate = (root / asset).resolve()
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            raise ValueError('allowed assets must be inside the report directory')
        if not candidate.exists():
            raise ValueError('allowed asset does not exist: %s' % asset)
        if candidate.is_dir():
            if not relative.parts or any(p.startswith('.') or p.lower() in PRIVATE_DIRS for p in relative.parts):
                raise ValueError('choose an asset directory, not the report root or a private directory')
            directories.append(candidate)
        elif candidate.is_file() and (public_asset(relative) or (candidate.name == 'review-input.js'
                and all(not p.startswith('.') and p.lower() not in PRIVATE_DIRS for p in relative.parts))):
            files.add(candidate)
        else:
            raise ValueError('only image/font/style/HTML assets or the explicit review-input.js may be allowed')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.respond(send_body=True)

        def do_HEAD(self):
            self.respond(send_body=False)

        def respond(self, send_body):
            port = self.server.server_port
            if self.headers.get('Host', '').lower() not in ('localhost:%d' % port, '127.0.0.1:%d' % port):
                self.send_error(403, 'Loopback host required')
                return
            try:
                parsed = urlsplit(self.path)
                raw = unquote(parsed.path, errors='strict')
                if (parsed.scheme or parsed.netloc or not raw.startswith('/') or '\\' in raw
                        or '\x00' in raw or any(part in ('.', '..') for part in raw.split('/'))):
                    self.send_error(403, 'Invalid path')
                    return
                if raw == '/':
                    self.send_response(302)
                    self.send_header('Location', '/' + quote(report.name))
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                candidate = (root / raw.lstrip('/')).resolve()
                relative = candidate.relative_to(root)
                allowed = candidate in files or (
                    public_asset(relative) and any(candidate.is_relative_to(d) for d in directories))
                if not allowed or not candidate.is_file():
                    self.send_error(404, 'Not a served report asset')
                    return
                # Resolving symlinks above prevents an allowed directory escaping the root.
                with candidate.open('rb') as stream:
                    self.send_response(200)
                    mime = mimetypes.guess_type(candidate.name)[0] or 'application/octet-stream'
                    self.send_header('Content-Type', mime + ('; charset=utf-8' if mime == 'text/html' else ''))
                    self.send_header('Content-Length', str(candidate.stat().st_size))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.send_header('Referrer-Policy', 'no-referrer')
                    self.send_header('Content-Security-Policy',
                                     "default-src 'none'; img-src 'self' data: blob:; "
                                     "style-src 'self' 'unsafe-inline'; font-src 'self'; "
                                     + ("script-src 'self' 'unsafe-inline'; " if mime == 'text/html' else "script-src 'none'; ")
                                     + "connect-src 'none'; object-src 'none'; base-uri 'none'; "
                                     "frame-ancestors 'none'; form-action 'none'")
                    self.end_headers()
                    if send_body:
                        while chunk := stream.read(64 * 1024):
                            self.wfile.write(chunk)
            except (ValueError, UnicodeError):
                self.send_error(403, 'Invalid path')
            except OSError:
                self.send_error(404, 'Report asset unavailable')

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('report', type=Path)
    parser.add_argument('--port', type=int, default=0, help='loopback port; 0 selects a free port')
    parser.add_argument('--allow-asset', action='append', default=[], metavar='PATH',
                        help='allow a file or asset directory beneath the report directory (repeatable)')
    args = parser.parse_args()
    report = args.report.expanduser().resolve()
    if not report.is_file() or report.suffix.lower() not in ('.html', '.htm'):
        parser.error('report must be an existing HTML file')
    if not 0 <= args.port <= 65535:
        parser.error('port must be between 0 and 65535')
    try:
        handler = make_handler(report, args.allow_asset)
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    with server:
        print('http://localhost:%d/%s' % (server.server_port, quote(report.name)), flush=True)
        print('Keep this process running until the owner is done. Ctrl-C stops it.', flush=True)
        print('To return to the same browser rulings, reuse --port %d and the same storage_key.' % server.server_port, flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
