"""Loopback-only dashboard with a fixed platform setup launcher."""
import atexit
import os
from pathlib import Path
import secrets
import sys
from urllib.parse import urlsplit
from flask import Flask, abort, jsonify, render_template, request, session, Response
from . import __version__
from .service import Manager
from .storage import Store
from .tools import diagnostics, tool_sources
from .setup_launcher import SetupLauncher


def create_app(data_dir=None, testing=False, **manager_options):
    root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    folder = Path(data_dir or root / "data")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not testing:
        folder.chmod(0o700)
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16_384,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict",
                      TESTING=testing)
    store = Store(folder / "history.sqlite3")
    if not testing:
        store.path.chmod(0o600)
    manager_options.setdefault("allow_live", True)
    manager = Manager(store, folder, **manager_options)
    setup = SetupLauncher(root, folder)
    app.extensions.update(echo_store=store, echo_manager=manager, echo_setup=setup)
    atexit.register(manager.close)
    cached = {"value": None}

    @app.before_request
    def boundary():
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            abort(403, "Local access only")
        if request.host.split(":")[0] not in {"localhost", "127.0.0.1"}:
            abort(403, "Invalid Host header")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                abort(403, "Cross-origin request blocked")
            expected = session.get("csrf")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not expected or not secrets.compare_digest(expected, supplied):
                abort(403, "Reload dashboard before submitting")

    @app.after_request
    def headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def error(exc):
        return jsonify(error=exc.description), exc.code

    @app.get("/")
    def index():
        session.setdefault("csrf", secrets.token_hex(32))
        return render_template("index.html", csrf=session["csrf"], version=__version__,
                               native_windows=sys.platform == "win32", native_macos=sys.platform == "darwin",
                               assessment_enabled=manager.allow_live)

    @app.get("/api/tools")
    def tools():
        # Tool help/version checks only. Never install software from HTTP requests.
        if cached["value"] is None or request.args.get("refresh") == "1":
            cached["value"] = diagnostics()
        return jsonify(cached["value"])

    @app.get("/api/tool-sources")
    def sources():
        return jsonify(tool_sources())

    @app.post("/api/setup-tools")
    def setup_tools():
        if request.get_json(silent=True) != {}:
            abort(400, "This action takes no commands, paths or installer options.")
        with setup.guard, manager.lock:
            if manager.active:
                abort(409, "Stop or finish the current assessment before setting up tools.")
            try:
                result = setup.launch()
            except ValueError as exc:
                abort(400, str(exc))
            except RuntimeError as exc:
                abort(409, str(exc))
            except OSError:
                abort(400, "Tool setup could not start. Check the setup guide for your platform and retry.")
        return jsonify(result), 202

    @app.get("/api/setup-status")
    def setup_status():
        return jsonify(setup.status())

    @app.get("/api/jobs")
    def jobs():
        return jsonify([{key: job[key] for key in ("id", "domain", "status", "created")}
                        for job in store.recent(include_demos=False)])

    @app.post("/api/jobs")
    def start():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            abort(400, "Expected a JSON object")
        try:
            with setup.guard:
                if setup.busy():
                    raise RuntimeError("Tool setup is still running or its terminal is open. Finish setup before starting an assessment.")
                job_id = manager.start(payload)
        except ValueError as exc:
            abort(400, str(exc))
        except RuntimeError as exc:
            abort(409, str(exc))
        return jsonify(id=job_id), 202

    def get_job(job_id):
        if len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            abort(404)
        job = store.get(job_id)
        if not job or job.get("demo") is True:
            abort(404)
        return job

    @app.get("/api/jobs/<job_id>")
    def job(job_id):
        return jsonify(get_job(job_id))

    @app.post("/api/jobs/<job_id>/cancel")
    def cancel(job_id):
        get_job(job_id)
        return jsonify(requested=manager.cancel(job_id))

    @app.get("/reports/<job_id>.html")
    def report(job_id):
        job = get_job(job_id)
        response = Response(render_template("report.html", job=job), mimetype="text/html")
        if request.args.get("download") == "1":
            response.headers["Content-Disposition"] = f'attachment; filename="echo-report-{job_id}.html"'
        return response

    @app.get("/reports/<job_id>.json")
    def report_json(job_id):
        response = jsonify(get_job(job_id))
        response.headers["Content-Disposition"] = f'attachment; filename="echo-report-{job_id}.json"'
        return response

    return app
