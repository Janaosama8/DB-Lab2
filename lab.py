
import os
from html import escape

from flask import Flask, request, redirect, session
import pymysql
import bcrypt
from dotenv import load_dotenv

# Load environment variables from the file named "env"
load_dotenv("env")

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY is missing from the env file")

app.secret_key = secret_key
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# Connect to MySQL database
def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "registration"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


# Login page
@app.route("/")
def home():
    return """
    <h2>Login Application</h2>

    <form action="/login" method="POST">
        <label>Email:</label>
        <input type="email" name="email" required maxlength="255">
        <br><br>

        <label>Password:</label>
        <input type="password" name="password" required>
        <br><br>

        <button type="submit">Login</button>
    </form>

    <p>Don't have an account?
       <a href="/register">Register</a></p>
    """


# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return """
        <h2>Create Account</h2>

        <form method="POST" action="/register"
              onsubmit="return validateForm()">

            <label>Name:</label>
            <input type="text" name="name" id="name"
                   required maxlength="100">
            <br><br>

            <label>Email:</label>
            <input type="email" name="email" id="email"
                   required maxlength="255">
            <br><br>

            <label>Password:</label>
            <input type="password" name="password" id="password"
                   required minlength="8">
            <br><br>

            <label>Confirm Password:</label>
            <input type="password" name="confirm_password"
                   id="confirm_password" required>
            <br><br>

            <p id="error" style="color:red;"></p>

            <button type="submit">Register</button>
        </form>

        <p><a href="/">Back to Login</a></p>

        <script>
        function validateForm() {
            const name =
                document.getElementById("name").value.trim();
            const email =
                document.getElementById("email").value.trim();
            const password =
                document.getElementById("password").value;
            const confirmPassword =
                document.getElementById("confirm_password").value;
            const error =
                document.getElementById("error");

            error.textContent = "";

            if (name.length === 0 || name.length > 100) {
                error.textContent =
                    "Name is required (maximum 100 characters).";
                return false;
            }

            if (email.length === 0 || email.length > 255) {
                error.textContent = "Please enter a valid email.";
                return false;
            }

            if (password.length < 8) {
                error.textContent =
                    "Password must be at least 8 characters.";
                return false;
            }

            if (password !== confirmPassword) {
                error.textContent = "Passwords do not match.";
                return false;
            }

            return true;
        }
        </script>
        """

    # Get submitted registration data
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Server-side validation
    errors = []

    if not name or len(name) > 100:
        errors.append(
            "Name is required and must be at most 100 characters."
        )

    if not email or len(email) > 255 or "@" not in email:
        errors.append("Please enter a valid email address.")

    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        return (
            "<h2>Registration Errors</h2><ul>"
            + "".join(
                f"<li>{escape(error)}</li>" for error in errors
            )
            + '</ul><a href="/register">Try again</a>'
        ), 400

    # Hash the password before storing it
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (email, name, password_hash)
                VALUES (%s, %s, %s)
                """,
                (email, name, password_hash)
            )

            user_id = cursor.lastrowid

        connection.commit()

        # Log in the newly registered user
        session.clear()
        session["user_id"] = user_id
        session["name"] = name

        return redirect("/welcome", code=303)

    except pymysql.err.IntegrityError:
        connection.rollback()

        return """
        <h2>Email Already Exists</h2>
        <p>This email is already registered.</p>
        <a href="/register">Try another email</a>
        """, 409

    finally:
        connection.close()


# Login
@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or len(email) > 255 or not password:
        return (
            '<h2>Invalid email or password.</h2>'
            '<a href="/">Try again</a>'
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, name, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

        if user:
            stored_hash = user[2].encode("utf-8")

            if bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash
            ):
                session.clear()
                session["user_id"] = user[0]
                session["name"] = user[1]

                return redirect("/welcome", code=303)

        return (
            '<h2>Invalid email or password.</h2>'
            '<a href="/">Try again</a>'
        ), 401

    finally:
        connection.close()


# Welcome page - requires login
@app.route("/welcome")
def welcome():

    if "user_id" not in session:
        return redirect("/")

    safe_name = escape(session.get("name", "User"))

    return f"""
    <h2>Welcome, {safe_name}!</h2>
    <p>You are logged in successfully.</p>
    <a href="/logout">Logout</a>
    """


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
