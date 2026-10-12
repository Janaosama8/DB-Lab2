
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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f2f4f7;
                padding: 25px 12px;
            }}
            .container {{
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
            }}
            input, button {{
                box-sizing: border-box;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            button {{
                background: white;
                color: #333;
                cursor: pointer;
            }}
            a {{ color: #333; }}
            .add-form {{
                display: flex;
                gap: 8px;
            }}
            .add-form input {{
                flex: 1;
                min-width: 0;
            }}
            .add-form button {{
                width: 65px;
            }}
            .task {{
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px 0;
                border-bottom: 1px solid #ddd;
            }}
            .task form {{
                margin: 0;
            }}
            .task input[type="checkbox"] {{
                width: 18px;
                height: 18px;
                cursor: pointer;
            }}
            .edit-form {{
                display: flex;
                flex: 1;
                gap: 5px;
                min-width: 0;
            }}
            .edit-form input {{
                width: 100%;
                min-width: 0;
            }}
            .done {{
                text-decoration: line-through;
                color: gray;
            }}
            .error {{
                color: red;
            }}
            .counter {{
                background: #eef5ff;
                padding: 12px;
                border-radius: 6px;
                margin: 15px 0;
            }}
            .filters {{
                margin: 15px 0;
            }}
            .filters a {{
                margin-right: 10px;
            }}
            @media (max-width: 450px) {{
                .task {{
                    flex-wrap: wrap;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">{content}</div>
    </body>
    </html>
    """


def error_page(message, back="/"):
    return page("Error", f"""
        <p class="error">{escape(message)}</p>
        <a href="{back}">Go back</a>
    """)


@app.route("/")
def home():
    return page("Login", """
        <h2>Login</h2>
        <form method="POST" action="/login">
            <p>
                <label>Email</label><br>
                <input type="email" name="email"
                       placeholder="Enter your email" required>
            </p>
            <p>
                <label>Password</label><br>
                <input type="password" name="password"
                       placeholder="Enter your password" required>
            </p>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="/register">Register</a></p>
    """)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return page("Register", """
            <h2>Register</h2>
            <form method="POST">
                <p>
                    <label>Name</label><br>
                    <input name="name" placeholder="Enter your name"
                           maxlength="100" required>
                </p>
                <p>
                    <label>Email</label><br>
                    <input type="email" name="email"
                           placeholder="Enter your email" required>
                </p>
                <p>
                    <label>Password</label><br>
                    <input type="password" name="password"
                           placeholder="Enter your password" required>
                </p>
                <p>
                    <label>Confirm Password</label><br>
                    <input type="password" name="confirm"
                           placeholder="Confirm your password" required>
                </p>
                <button type="submit">Register</button>
            </form>
            <p>Already registered? <a href="/">Login</a></p>
        """)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    if not name:
        return error_page("Name is required", "/register")
    if not email:
        return error_page("Email is required", "/register")
    if not password:
        return error_page("Password is required", "/register")
    if not confirm:
        return error_page("Confirm password is required", "/register")
    if password != confirm:
        return error_page("Passwords do not match", "/register")

    hashed = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()
    ).decode()

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO users (name, email, password_hash)
                   VALUES (%s, %s, %s)""",
                (name, email, hashed)
            )
        db.commit()
    except pymysql.err.IntegrityError:
         return page("Register", f"""
            <h2>Register</h2>

            <p style="color: red;">Email already exists. .</p>

            <form method="POST">
                <p>
                    <label>Name</label><br>
                    <input name="name" value="{escape(name)}"
                           maxlength="100" required>
                </p>

                <p>
                    <label>Email</label><br>
                    <input type="email" name="email" value="{escape(email)}"
                           required>
                             </p>

                <p>
                    <label>Password</label><br>
                    <input type="password" name="password" required>
                </p>

                <p>
                    <label>Confirm Password</label><br>
                    <input type="password" name="confirm" required>
                </p>

                <button type="submit">Register</button>
            </form>

            <p>Already registered? <a href="/">Login</a></p>
        """)
    finally:
        db.close()

    return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email:
        return error_page("Email is required")
    if not password:
        return error_page("Password is required")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT user_id, name, password_hash
                   FROM users WHERE email = %s""",
                (email,)
            )
            user = cur.fetchone()
    finally:
        db.close()

    if not user or not bcrypt.checkpw(
        password.encode(), user["password_hash"].encode()
    ):
        return error_page("Invalid email or password")

    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect("/todos")


@app.route("/todos", methods=["GET", "POST"])
def todos():
    if not session.get("user_id"):
        return redirect("/")

    user_id = session["user_id"]
    message = ""

    filter_by = request.args.get("filter", "all")
    if filter_by not in ("all", "open", "done"):
        filter_by = "all"

    if request.method == "POST":
        title = request.form.get("title", "").strip()

        if not title:
            message = "Title is required"
        elif len(title) > 200:
            message = "Title is too long (200 characters at most)"
        else:
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute(
                        """INSERT INTO todos (user_id, title)
                           VALUES (%s, %s)""",
                        (user_id, title)
                    )
                db.commit()
            finally:
                db.close()

            return redirect("/todos?filter=" + filter_by)

    query = """
        SELECT todo_id, title, is_done
        FROM todos
        WHERE user_id = %s
    """
    params = [user_id]

    if filter_by == "open":
        query += " AND is_done = 0"
    elif filter_by == "done":
        query += " AND is_done = 1"

    query += " ORDER BY created_at DESC, todo_id DESC"

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(query, params)
            tasks = cur.fetchall()

            cur.execute(
                """SELECT COUNT(*) AS open_count
                   FROM todos
                   WHERE user_id = %s AND is_done = 0""",
                (user_id,)
            )
            open_count = cur.fetchone()["open_count"]
    finally:
        db.close()

    task_html = ""

    for task in tasks:
        tid = task["todo_id"]
        title = escape(task["title"])
        checked = "checked" if task["is_done"] else ""
        done_class = "done" if task["is_done"] else ""

        task_html += f"""
        <div class="task">
            <form method="POST" action="/todos/{tid}/toggle">
                <input type="checkbox" {checked}
                       onchange="this.form.submit()">
            </form>

            <form class="edit-form" method="POST"
                  action="/todos/{tid}/edit">
                <input class="{done_class}" name="title"
                       value="{title}" maxlength="200" required>
                <button type="submit">Save</button>
            </form>

            <form method="POST" action="/todos/{tid}/delete"
                  onsubmit="return confirm('Are you sure you want to delete this task?');">
                <button type="submit">Delete</button>
            </form>
        </div>
        """

    all_style = "font-weight:bold;" if filter_by == "all" else ""
    open_style = "font-weight:bold;" if filter_by == "open" else ""
    done_style = "font-weight:bold;" if filter_by == "done" else ""

    return page("My Tasks", f"""
        <h2>To-Do List</h2>
        <p>Welcome, {escape(session.get("name", ""))}</p>

        <div class="counter">
            <strong>Open tasks: {open_count}</strong>
        </div>

        <form class="add-form" method="POST">
            <input name="title"
                   placeholder="What needs to be done?"
                   maxlength="200" required>
            <button type="submit">Add</button>
        </form>

        <p class="error">{escape(message)}</p>

        <h3>Filter Tasks</h3>
        <div class="filters">
            <a href="/todos?filter=all" style="{all_style}">All</a>
            <a href="/todos?filter=open" style="{open_style}">Open</a>
            <a href="/todos?filter=done" style="{done_style}">Done</a>
        </div>

        {task_html if tasks else "<p>No tasks to display.</p>"}

        <p><a href="/logout">Logout</a></p>
    """)


@app.route("/todos/<int:tid>/toggle", methods=["POST"])
def toggle(tid):
    if not session.get("user_id"):
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """UPDATE todos SET is_done = 1 - is_done
                   WHERE todo_id = %s AND user_id = %s""",
                (tid, session["user_id"])
            )
        db.commit()
    finally:
        db.close()

    return redirect("/todos")


@app.route("/todos/<int:tid>/edit", methods=["POST"])
def edit(tid):
    if not session.get("user_id"):
        return redirect("/")

    title = request.form.get("title", "").strip()

    if not title:
        return error_page("Title is required", "/todos")
    if len(title) > 200:
        return error_page(
            "Title is too long (200 characters at most)", "/todos"
        )

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """UPDATE todos SET title = %s
                   WHERE todo_id = %s AND user_id = %s""",
                (title, tid, session["user_id"])
            )
        db.commit()
    finally:
        db.close()

    return redirect("/todos")


@app.route("/todos/<int:tid>/delete", methods=["POST"])
def delete(tid):
    if not session.get("user_id"):
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """DELETE FROM todos
                   WHERE todo_id = %s AND user_id = %s""",
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
