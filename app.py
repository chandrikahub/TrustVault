
import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, session,
    flash, g, render_template_string, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = BASE_DIR / "uploads"

INSTANCE_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, instance_path=str(INSTANCE_DIR))
app.config["SECRET_KEY"] = os.environ.get(
    "TRUSTVAULT_SECRET_KEY", "dev-only-change-this-before-deployment"
)
app.config["DATABASE"] = str(INSTANCE_DIR / "trustvault.db")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

def connect_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS permissions (
                document_id INTEGER NOT NULL REFERENCES documents(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                PRIMARY KEY(document_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                document_id INTEGER,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create a demo administrator only if no users exist.
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("ChangeMe123!"), "admin")
            )

def audit(db, user_id, action, document_id=None, details=""):
    db.execute(
        """INSERT INTO audit_logs
           (user_id, action, document_id, details)
           VALUES (?, ?, ?, ?)""",
        (user_id, action, document_id, details)
    )

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with connect_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                audit(db, user["id"], "login", details="Successful login")
                return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template_string(PAGE, title="Login", content="""
        <h2>Sign in to TrustVault</h2>
        <form method="post">
            <label>Username</label>
            <input name="username" required autocomplete="username">
            <label>Password</label>
            <input name="password" type="password" required
                   autocomplete="current-password">
            <button>Login</button>
        </form>
        <p class="hint">First run demo: admin / ChangeMe123!</p>
        <p>Change the demo password before using this beyond local testing.</p>
    """)

@app.route("/dashboard")
@login_required
def dashboard():
    with connect_db() as db:
        if session["role"] == "admin":
            documents = db.execute("""
                SELECT d.*, u.username AS owner_name
                FROM documents d JOIN users u ON u.id = d.owner_id
                ORDER BY d.id DESC
            """).fetchall()
        else:
            documents = db.execute("""
                SELECT DISTINCT d.*, u.username AS owner_name
                FROM documents d
                JOIN users u ON u.id = d.owner_id
                LEFT JOIN permissions p ON p.document_id = d.id
                WHERE d.owner_id = ? OR p.user_id = ?
                ORDER BY d.id DESC
            """, (session["user_id"], session["user_id"])).fetchall()

    rows = "".join(
        f"<li>{d['original_name']} — owner: {d['owner_name']} "
        f"<a href='/download/{d['id']}'>Download</a></li>"
        for d in documents
    ) or "<li>No documents available yet.</li>"

    admin_link = (
        '<p><a href="/admin/users">Manage users</a> | '
        '<a href="/admin/audit">Audit history</a></p>'
        '<a href="/admin/share">Share documents</a></p>'
        if session["role"] == "admin" else ""
    )

    content = f"""
        <h2>Welcome, {session['username']}!</h2>
        <p>Role: {session['role']}</p>
        <h3>Your accessible documents</h3>
        <ul>{rows}</ul>
        <h3>Upload a document</h3>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="document" required>
            <button>Upload</button>
        </form>
        {admin_link}
        <form action="/logout" method="post"><button>Logout</button></form>
    """
    return render_template_string(PAGE, title="Dashboard", content=content)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("document")
    if not file or not file.filename:
        flash("Please choose a file.")
        return redirect(url_for("dashboard"))

    import uuid
    from werkzeug.utils import secure_filename

    safe_name = secure_filename(file.filename)
    if not safe_name:
        flash("Invalid filename.")
        return redirect(url_for("dashboard"))

    stored_name = uuid.uuid4().hex
    file.save(UPLOAD_DIR / stored_name)

    with connect_db() as db:
        cur = db.execute(
            """INSERT INTO documents (owner_id, original_name, stored_name)
               VALUES (?, ?, ?)""",
            (session["user_id"], safe_name, stored_name)
        )
        audit(db, session["user_id"], "upload", cur.lastrowid,
              f"Uploaded {safe_name}")

    flash("Document uploaded successfully.")
    return redirect(url_for("dashboard"))

@app.route("/download/<int:document_id>")
@login_required
def download(document_id):
    from flask import send_file

    with connect_db() as db:
        doc = db.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()

        if not doc:
            abort(404)

        allowed = (
            session["role"] == "admin"
            or doc["owner_id"] == session["user_id"]
            or db.execute(
                """SELECT 1 FROM permissions
                   WHERE document_id = ? AND user_id = ?""",
                (document_id, session["user_id"])
            ).fetchone()
        )

        if not allowed:
            audit(db, session["user_id"], "access_denied", document_id,
                  "Unauthorized download attempt")
            abort(403)

        audit(db, session["user_id"], "download", document_id,
              f"Downloaded {doc['original_name']}")
        stored_name = doc["stored_name"]
        original_name = doc["original_name"]

    path = UPLOAD_DIR / stored_name
    if not path.is_file():
        abort(404)

    return send_file(path, as_attachment=True, download_name=original_name)

@app.route("/admin/users", methods=["GET", "POST"])
@login_required
def admin_users():
    if session["role"] != "admin":
        abort(403)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if len(username) < 3 or len(password) < 10 or role not in ("admin", "user"):
            flash("Use a username of 3+ characters and password of 10+ characters.")
        else:
            try:
                with connect_db() as db:
                    db.execute(
                        """INSERT INTO users (username, password_hash, role)
                           VALUES (?, ?, ?)""",
                        (username, generate_password_hash(password), role)
                    )
                    audit(db, session["user_id"], "create_user",
                          details=f"Created account {username} ({role})")
                flash("User created.")
            except sqlite3.IntegrityError:
                flash("That username already exists.")

        return redirect(url_for("admin_users"))

    with connect_db() as db:
        users = db.execute(
            "SELECT id, username, role FROM users ORDER BY id"
        ).fetchall()

    rows = "".join(
        f"<li>{u['username']} — {u['role']} (ID {u['id']})</li>"
        for u in users
    )
    return render_template_string(PAGE, title="Manage users", content=f"""
        <h2>Create user</h2>
        <form method="post">
            <label>Username</label><input name="username" required>
            <label>Password (10+ characters)</label>
            <input name="password" type="password" required minlength="10">
            <label>Role</label>
            <select name="role">
                <option value="user">User</option>
                <option value="admin">Admin</option>
            </select>
            <button>Create account</button>
        </form>
        <h3>Existing users</h3><ul>{rows}</ul>
        <p><a href="/dashboard">Back to dashboard</a></p>
    """)

@app.route("/admin/audit")
@login_required
def admin_audit():
    if session["role"] != "admin":
        abort(403)

    with connect_db() as db:
        logs = db.execute("""
            SELECT a.*, u.username
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.id DESC LIMIT 200
        """).fetchall()

    rows = "".join(
        f"<tr><td>{r['created_at']}</td><td>{r['username'] or 'Unknown'}</td>"
        f"<td>{r['action']}</td><td>{r['document_id'] or ''}</td>"
        f"<td>{r['details'] or ''}</td></tr>"
        for r in logs
    )
    return render_template_string(PAGE, title="Audit history", content=f"""
        <h2>Audit history</h2>
        <table><tr><th>Time</th><th>User</th><th>Action</th>
        <th>Document</th><th>Details</th></tr>{rows}</table>
        <p><a href="/dashboard">Back to dashboard</a></p>
    """)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    with connect_db() as db:
        audit(db, session["user_id"], "logout", details="User logged out")
    session.clear()
    return redirect(url_for("login"))

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TrustVault - {{ title }}</title>
<style>
body { font-family: Arial, sans-serif; background:#0f172a; color:#f8fafc;
       max-width:850px; margin:40px auto; padding:20px; }
main { background:#1e293b; padding:28px; border-radius:14px; }
h1 { color:#38bdf8; }
input, select { display:block; box-sizing:border-box; width:100%;
                padding:10px; margin:8px 0 16px; }
button { background:#38bdf8; padding:10px 18px; border:0;
         border-radius:6px; cursor:pointer; }
a { color:#7dd3fc; }
li { margin:12px 0; overflow-wrap:anywhere; }
table { border-collapse:collapse; width:100%; font-size:14px; }
td, th { border:1px solid #475569; padding:8px; text-align:left; }
.flash { color:#fbbf24; }
.hint { color:#cbd5e1; }
</style>
</head>
<body><h1>🔐 TrustVault</h1><main>
{% for message in get_flashed_messages() %}
<p class="flash">{{ message }}</p>
{% endfor %}
{{ content|safe }}
</main></body></html>
"""

with app.app_context():
    init_db()


@app.route("/admin/share", methods=["GET", "POST"])
@login_required
def share_document():
    from flask import request

    if session.get("role") != "admin":
        abort(403)

    message = ""

    with connect_db() as db:
        if request.method == "POST":
            document_id = request.form.get("document_id", type=int)
            user_id = request.form.get("user_id", type=int)

            doc = db.execute(
                "SELECT id FROM documents WHERE id = ?",
                (document_id,)
            ).fetchone()
            user = db.execute(
                "SELECT id FROM users WHERE id = ? AND role = 'user'",
                (user_id,)
            ).fetchone()

            if not doc or not user:
                message = "Please select a valid document and user."
            else:
                db.execute(
                    """INSERT OR IGNORE INTO permissions
                       (document_id, user_id) VALUES (?, ?)""",
                    (document_id, user_id)
                )
                audit(
                    db, session["user_id"], "share",
                    document_id, f"Shared document with user {user_id}"
                )
                message = "Document sharing permission saved!"

        documents = db.execute(
            "SELECT id, original_name FROM documents ORDER BY id DESC"
        ).fetchall()
        users = db.execute(
            "SELECT id, username FROM users WHERE role = 'user' ORDER BY username"
        ).fetchall()

    document_options = "".join(
        f'<option value="{d["id"]}">{d["id"]} - {d["original_name"]}</option>'
        for d in documents
    )
    user_options = "".join(
        f'<option value="{u["id"]}">{u["username"]}</option>'
        for u in users
    )

    return f"""
    <h2>Share a Document</h2>
    <p>{message}</p>
    <form method="post">
      <label>Document</label>
      <select name="document_id" required>{document_options}</select>
      <br><br>
      <label>Share with user</label>
      <select name="user_id" required>{user_options}</select>
      <br><br>
      <button type="submit">Grant Access</button>
    </form>
    <p><a href="/dashboard">Back to Dashboard</a></p>
    """
if __name__ == "__main__":
    app.run(debug=True)
