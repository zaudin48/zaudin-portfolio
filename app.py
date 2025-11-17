# app.py (clean, merged, skills + experience + fixed admin)
import os
import sqlite3
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, jsonify,
    session, g, url_for, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

# ----------------------------
# Configuration
# ----------------------------
BASE = Path(__file__).parent
DB_PATH = BASE / "instance" / "portfolio.db"
UPLOAD_FOLDER = BASE / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "change-me")

# SMTP (optional)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
CONTACT_RECIPIENT_EMAIL = os.getenv("CONTACT_RECIPIENT_EMAIL", "zaudinkhan16@gmail.com")


# ----------------------------
# DB Helpers
# ----------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, "_database", None)
    if db:
        db.close()

def query_db(query, args=(), one=False, commit=False):
    cur = get_db().execute(query, args)
    if commit:
        get_db().commit()
        cur.close()
        return None
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


# ----------------------------
# Init DB (tables + defaults)
# ----------------------------
def init_db():
    db = get_db()

    # admin
    db.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        pfp TEXT
    );
    """)
    # ensure default admin row (id = 1)
    admin = query_db("SELECT * FROM admin WHERE id = 1", one=True)
    if not admin:
        db.execute(
            "INSERT INTO admin (id, username, password_hash, pfp) VALUES (1, ?, ?, ?)",
            ("admin", generate_password_hash("admin"), "/static/uploads/default_pfp.png")
        )
        db.commit()

    # projects
    db.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        link TEXT,
        img_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # contact (single-row table id=1)
    db.execute("""
    CREATE TABLE IF NOT EXISTS contact (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT,
        email TEXT,
        phone TEXT,
        whatsapp TEXT,
        address TEXT,
        hero_title TEXT,
        hero_sub TEXT
    );
    """)
    c = query_db("SELECT * FROM contact WHERE id = 1", one=True)
    if not c:
        db.execute("""
            INSERT INTO contact (id, name, email, phone, whatsapp, address, hero_title, hero_sub)
            VALUES (1,?,?,?,?,?,?,?)
        """, (
            "Zavudin Khan",
            "zaudinkhan16@gmail.com",
            "8698240158",
            "8698240158",
            "House No. 2286, Katarwada, IDC, Bicholim, Goa - 403529",
            "Let's build something great",
            "Reach out to discuss projects, collabs or just say hi."
        ))
        db.commit()

    # skills table
    db.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        percentage INTEGER NOT NULL
    );
    """)

    # experience table (you provided schema - using AUTOINCREMENT)
    db.execute("""
    CREATE TABLE IF NOT EXISTS experience (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        years INTEGER NOT NULL
    );
    """)
    # ensure a single experience row exists with id = 1 (if none, insert default)
    exp = query_db("SELECT * FROM experience WHERE id = 1", one=True)
    if not exp:
        # insert id 1 manually: sqlite will allow since AUTOINCREMENT but we set id explicitly
        db.execute("INSERT INTO experience (id, years) VALUES (1, ?)", (2,))
        db.commit()


# ----------------------------
# Utility helpers for templates
# ----------------------------
def get_admin_pfp():
    r = query_db("SELECT pfp FROM admin WHERE id = 1", one=True)
    pfp = r["pfp"] if r and r["pfp"] else "/static/uploads/default_pfp.png"
    return pfp

def get_project_count():
    r = query_db("SELECT COUNT(*) as c FROM projects", one=True)
    return int(r["c"]) if r else 0

def get_contact_info():
    r = query_db("SELECT * FROM contact WHERE id = 1", one=True)
    return dict(r) if r else {}

# ----------------------------
# Main routes (public)
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/projects")
def projects_page():
    return render_template("projects.html")

@app.route("/contact")
def contact_page():
    row = query_db("SELECT * FROM contact WHERE id = 1", one=True)
    contact = dict(row) if row else {}
    # whatsapp normalized
    w = (contact.get("whatsapp") or contact.get("phone") or "").replace("+", "").replace(" ", "")
    if len(w) == 10:
        w = "91" + w
    contact["wa_link"] = f"https://wa.me/{w}" if w else "#"
    return render_template("contact.html", contact=contact)


# ----------------------------
# API endpoints
# ----------------------------
@app.route("/api/projects")
def api_projects():
    rows = query_db("SELECT id,title,description,link,img_url,created_at FROM projects ORDER BY created_at DESC")
    return jsonify([dict(r) for r in rows])

@app.route("/api/profile")
def api_profile():
    row = query_db("SELECT username, pfp FROM admin WHERE id = 1", one=True)
    if not row:
        return jsonify({"username": "admin", "pfp": "/static/uploads/default_pfp.png"})
    pfp = row["pfp"]
    if not pfp or str(pfp).strip() == "":
        pfp = "/static/uploads/default_pfp.png"
    return jsonify({"username": row["username"], "pfp": pfp})

@app.route("/api/contact-info")
def api_contact():
    row = query_db("SELECT * FROM contact WHERE id = 1", one=True)
    return jsonify(dict(row) if row else {})

@app.route("/api/skills")
def api_skills():
    rows = query_db("SELECT * FROM skills ORDER BY id ASC")
    return jsonify([dict(r) for r in rows])

@app.route("/api/experience")
def api_experience():
    r = query_db("SELECT years FROM experience WHERE id = 1", one=True)
    return jsonify({"years": r["years"] if r else None})


# ----------------------------
# Authentication + Admin UI
# ----------------------------
@app.route("/super-secret-login")
def super_secret_login():
    return render_template("admin_login.html")

@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form.get("username")
    password = request.form.get("password")
    row = query_db("SELECT * FROM admin WHERE username=?", (username,), one=True)
    if row and check_password_hash(row["password_hash"], password):
        session["admin"] = row["username"]
        return redirect("/admin")
    return "Login failed", 401

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/")

@app.route("/admin-reset")
def admin_reset():
    session.pop("admin", None)
    return "Session cleared."


# single admin dashboard route (renders admin.html with everything)
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/super-secret-login")

    skills = query_db("SELECT * FROM skills ORDER BY id ASC")
    years_row = query_db("SELECT years FROM experience WHERE id = 1", one=True)
    years = years_row["years"] if years_row else 0

    return render_template(
        "admin.html",
        skills=skills,
        years=years,
        pfp=get_admin_pfp(),
        project_count=get_project_count(),
        contact=get_contact_info()
    )


# ----------------------------
# Admin: username/password/contact updates
# ----------------------------
@app.route("/admin/change-username", methods=["POST"])
def change_username():
    if not session.get("admin"):
        return "Unauthorized", 401
    new_username = request.form.get("new_username")
    if not new_username:
        return "Missing username", 400
    query_db("UPDATE admin SET username=? WHERE id=1", (new_username,), commit=True)
    session["admin"] = new_username
    return redirect("/admin")

@app.route("/admin/change-password", methods=["POST"])
def change_password():
    if not session.get("admin"):
        return "Unauthorized", 401
    current_pw = request.form.get("current_pw")
    new_pw = request.form.get("new_pw")
    row = query_db("SELECT password_hash FROM admin WHERE id=1", one=True)
    if not row or not check_password_hash(row["password_hash"], current_pw):
        return "Incorrect current password", 400
    new_hash = generate_password_hash(new_pw)
    query_db("UPDATE admin SET password_hash=? WHERE id=1", (new_hash,), commit=True)
    return redirect("/admin")

@app.route("/admin/update-contact", methods=["POST"])
def admin_update_contact():
    if not session.get("admin"):
        return "Unauthorized", 401
    fields = ["name", "email", "phone", "whatsapp", "address", "hero_title", "hero_sub"]
    values = [request.form.get(f, "") for f in fields]
    query_db("""
        UPDATE contact SET name=?, email=?, phone=?, whatsapp=?, address=?, hero_title=?, hero_sub=? WHERE id=1
    """, values, commit=True)
    return redirect("/admin")


# ----------------------------
# Admin: experience update
# ----------------------------
@app.route("/admin/update-experience", methods=["POST"])
def update_experience():
    if not session.get("admin"):
        return "Unauthorized", 401
    years = request.form.get("years")
    try:
        years_i = int(years)
    except Exception:
        years_i = 0
    query_db("UPDATE experience SET years=? WHERE id=1", (years_i,), commit=True)
    return redirect("/admin")


# ----------------------------
# Skills CRUD (actions expected by admin.html forms)
# ----------------------------
@app.route("/admin/skills/add", methods=["POST"])
def skills_add():
    if not session.get("admin"):
        return "Unauthorized", 401
    label = request.form.get("label", "").strip()
    percentage = request.form.get("percentage", "0")
    try:
        percentage = int(percentage)
    except:
        percentage = 0
    if not label:
        return redirect("/admin")
    query_db("INSERT INTO skills (label, percentage) VALUES (?,?)", (label, percentage), commit=True)
    return redirect("/admin")

@app.route("/admin/skills/update/<int:id>", methods=["POST"])
def skills_update(id):
    if not session.get("admin"):
        return "Unauthorized", 401
    label = request.form.get("label", "").strip()
    percentage = request.form.get("percentage", "0")
    try:
        percentage = int(percentage)
    except:
        percentage = 0
    query_db("UPDATE skills SET label=?, percentage=? WHERE id=?", (label, percentage, id), commit=True)
    return redirect("/admin")

@app.route("/admin/skills/delete/<int:id>", methods=["POST"])
def skills_delete(id):
    if not session.get("admin"):
        return "Unauthorized", 401
    query_db("DELETE FROM skills WHERE id=?", (id,), commit=True)
    return redirect("/admin")


# ----------------------------
# Projects CRUD (uploads)
# ----------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

@app.route("/admin/upload", methods=["POST"])
def add_project():
    if not session.get("admin"):
        return "Unauthorized", 401
    title = request.form.get("title")
    desc = request.form.get("description")
    link = request.form.get("link")
    file = request.files.get("image")
    img_url = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(UPLOAD_FOLDER / filename)
        img_url = "/static/uploads/" + filename
    query_db("INSERT INTO projects (title, description, link, img_url) VALUES (?,?,?,?)",
             (title, desc, link, img_url), commit=True)
    return redirect("/admin")

@app.route("/admin/delete-project", methods=["POST"])
def delete_project():
    if not session.get("admin"):
        return "Unauthorized", 401
    pid = request.form.get("project_id")
    query_db("DELETE FROM projects WHERE id=?", (pid,), commit=True)
    return redirect("/admin")

@app.route("/admin/edit-project", methods=["POST"])
def edit_project():
    if not session.get("admin"):
        return "Unauthorized", 401
    pid = request.form.get("id")
    title = request.form.get("title")
    desc = request.form.get("description")
    link = request.form.get("link")
    file = request.files.get("image")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(UPLOAD_FOLDER / filename)
        img_url = "/static/uploads/" + filename
        query_db("UPDATE projects SET title=?, description=?, link=?, img_url=? WHERE id=?",
                 (title, desc, link, img_url, pid), commit=True)
    else:
        query_db("UPDATE projects SET title=?, description=?, link=? WHERE id=?",
                 (title, desc, link, pid), commit=True)
    return ("", 204)


# ----------------------------
# Profile pic upload/remove
# ----------------------------
@app.route("/admin/upload-pfp", methods=["POST"])
def upload_pfp():
    if not session.get("admin"):
        return "Unauthorized", 401
    file = request.files.get("pfp")
    if not file or not allowed_file(file.filename):
        return "Invalid file", 400
    filename = "pfp_" + secure_filename(file.filename)
    file.save(UPLOAD_FOLDER / filename)
    query_db("UPDATE admin SET pfp=? WHERE id=1", ("/static/uploads/" + filename,), commit=True)
    return redirect("/admin")

@app.route("/admin/remove-pfp", methods=["POST"])
def remove_pfp():
    if not session.get("admin"):
        return "Unauthorized", 401
    query_db("UPDATE admin SET pfp='' WHERE id=1", commit=True)
    return redirect("/admin")


# ----------------------------
# Contact form sending
# ----------------------------
@app.route("/contact/send", methods=["POST"])
def contact_send():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    msg = request.form.get("message")
    if not msg or not email:
        return "Missing fields", 400

    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        import smtplib
        from email.message import EmailMessage
        mail = EmailMessage()
        mail["Subject"] = f"Website contact from {name or email}"
        mail["From"] = SMTP_USER
        mail["To"] = CONTACT_RECIPIENT_EMAIL
        mail.set_content(f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n{msg}")
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(mail)
        except Exception as e:
            return f"Email failed: {e}", 500
        return "Sent", 200

    # fallback (no SMTP): accept but inform
    return "Received (SMTP not enabled)", 200


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    with app.app_context():
        init_db()
    PORT = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT, debug=False)
