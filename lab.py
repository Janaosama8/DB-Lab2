
import os
import pymysql
import bcrypt
from flask import Flask, request, redirect, session
from markupsafe import escape
from dotenv import load_dotenv

load_dotenv("env")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing from env file")


def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "registration"),
        port=int(os.getenv("DB_PORT", "3306")),
        cursorclass=pymysql.cursors.DictCursor
    )


def page(title, content):
    return f"""<html><head><title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{{font-family:Arial;background:#f2f4f7;padding:20px}}
    .box{{max-width:600px;margin:auto;background:white;padding:20px;border-radius:8px}}
    input,button{{padding:10px;border:1px solid #ddd;border-radius:5px;box-sizing:border-box}}
    button{{cursor:pointer}}a{{color:#333}}.error{{color:red}}
    .task,.form{{display:flex;align-items:center;gap:8px;margin:10px 0}}
    .form input,.edit input{{flex:1;min-width:0}}
    .done{{text-decoration:line-through;color:gray}}
    .counter{{background:#eef5ff;padding:12px}}
    </style></head><body><div class="box">{content}</div></body></html>"""


def error_page(message, back="/"):
    return page("Error", f'<p class="error">{escape(message)}</p><a href="{back}">Go back</a>')


def login_form():
    return page("Login", """
    <h2>Login</h2>
    <form method="POST" action="/login">
    <p>Email<br><input type="email" name="email" required></p>
    <p>Password<br><input type="password" name="password" required></p>
    <button>Login</button></form>
    <a href="/register">Register</a>""")


def register_form(message=""):
    return page("Register", f"""
    <h2>Register</h2>
    <p class="error">{escape(message)}</p>
    <form method="POST" action="/register">
    <p>Name<br><input name="name" maxlength="100" required></p>
    <p>Email<br><input type="email" name="email" required></p>
    <p>Password<br><input type="password" name="password"
    minlength="8" required></p>
    <p>Confirm Password<br><input type="password" name="confirm" required></p>
    <button>Register</button></form>
    <a href="/">Login</a>""")


def logged_in():
    return "user_id" in session


@app.route("/")
def home():
    return login_form()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return register_form(session.pop("register_message", ""))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    if not name or not email or not password or not confirm:
        session["register_message"] = "All fields are required"
        return redirect("/register")

    if len(password) < 8:
        session["register_message"] = "Password must be at least 8 characters"
        return redirect("/register")

    if password != confirm:
        session["register_message"] = "Passwords do not match"
        return redirect("/register")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db = get_db()

    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name,email,password_hash) VALUES (%s,%s,%s)",
                (name, email, hashed)
            )
        db.commit()
    except pymysql.err.IntegrityError:
        session["register_message"] = "Email already exists"
        return redirect("/register")
    finally:
        db.close()

    return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT user_id,name,password_hash FROM users WHERE email=%s",
                (email,)
            )
            user = cur.fetchone()
    finally:
        db.close()

    if not user or not bcrypt.checkpw(
        password.encode(), user["password_hash"].encode()
    ):
        return error_page("Invalid email or password")

    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect("/todos")


@app.route("/todos", methods=["GET", "POST"])
def todos():
    if not logged_in():
        return redirect("/")

    uid = session["user_id"]
    filter_by = request.args.get("filter", "all")
    if filter_by not in ("all", "open", "done"):
        filter_by = "all"

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title or len(title) > 200:
            message = "Enter a title up to 200 characters"
        else:
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute(
                        "INSERT INTO todos (user_id,title) VALUES (%s,%s)",
                        (uid, title)
                    )
                db.commit()
            finally:
                db.close()
            return redirect("/todos?filter=" + filter_by)
    else:
        message = ""

    query = "SELECT todo_id,title,is_done FROM todos WHERE user_id=%s"
    if filter_by == "open":
        query += " AND is_done=0"
    elif filter_by == "done":
        query += " AND is_done=1"
    query += " ORDER BY created_at DESC,todo_id DESC"

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(query, (uid,))
            tasks = cur.fetchall()
            cur.execute(
                "SELECT COUNT(*) AS n FROM todos WHERE user_id=%s AND is_done=0",
                (uid,)
            )
            count = cur.fetchone()["n"]
    finally:
        db.close()

    html = ""
    for t in tasks:
        tid = t["todo_id"]
        title = escape(t["title"])
        checked = "checked" if t["is_done"] else ""
        done = "done" if t["is_done"] else ""
        html += f"""
        <div class="task">
        <form method="POST" action="/todos/{tid}/toggle">
        <input type="checkbox" {checked}
        onchange="this.form.submit()"></form>
        <form class="edit" method="POST" action="/todos/{tid}/edit">
        <input name="title" value="{title}" class="{done}"
        maxlength="200" required>
        <button>Save</button></form>
        <form method="POST" action="/todos/{tid}/delete"
        onsubmit="return confirm('Delete this task?')">
        <button>Delete</button></form>
        </div>"""

    if not tasks:
        html = "<p>No tasks to display.</p>"

    filters = " | ".join(
        f'<a href="/todos?filter={v}">{v.title()}</a>'
        for v in ("all", "open", "done")
    )

    return page("My Tasks", f"""
    <h2>To-Do List</h2>
    <p>Welcome, {escape(session.get("name", ""))}</p>
    <p class="counter">Open tasks: {count}</p>
    <form method="POST" class="form">
    <input name="title" placeholder="New task" maxlength="200" required>
    <button>Add</button></form>
    <p class="error">{escape(message)}</p>
    <h3>Filter: {filters}</h3>
    {html}<a href="/logout">Logout</a>""")


@app.route("/todos/<int:tid>/toggle", methods=["POST"])
def toggle(tid):
    if not logged_in():
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE todos SET is_done=1-is_done "
                "WHERE todo_id=%s AND user_id=%s",
                (tid, session["user_id"])
            )
        db.commit()
    finally:
        db.close()

    return redirect("/todos")


@app.route("/todos/<int:tid>/edit", methods=["POST"])
def edit(tid):
    if not logged_in():
        return redirect("/")

    title = request.form.get("title", "").strip()
    if not title or len(title) > 200:
        return error_page("Title must contain 1 to 200 characters", "/todos")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE todos SET title=%s "
                "WHERE todo_id=%s AND user_id=%s",
                (title, tid, session["user_id"])
            )
        db.commit()
    finally:
        db.close()

    return redirect("/todos")


@app.route("/todos/<int:tid>/delete", methods=["POST"])
def delete(tid):
    if not logged_in():
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "DELETE FROM todos WHERE todo_id=%s AND user_id=%s",
                (tid, session["user_id"])
            )
        db.commit()
    finally:
        db.close()

    return redirect("/todos")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
