import os
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-secret")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # uploads: 4 MB at most
UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads")



def connect(database):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_db():
    """Lab 2 database (users, todos): one connection per request, closed at the end."""
    if "db" not in g:
        g.db = connect(os.getenv("DB_NAME", "registration"))
    return g.db


def get_lib_db():
    """Lab 3 database `library` (author, book): one connection per request."""
    if "lib_db" not in g:
        g.lib_db = connect(os.getenv("LIB_DB_NAME", "library"))
    return g.lib_db


@app.teardown_appcontext
def close_db(_exc):
    for key in ("db", "lib_db"):
        conn = g.pop(key, None)
        if conn is not None:
            conn.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:  
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped



def check_title(title):
    if not title:
        return ["Title is required"]
    if len(title) > 200:
        return ["Title is too long (200 characters at most)"]
    return []


def check_register(name, email, password, confirm):
    errors = []
    if not name:
        errors.append("Name is required")
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if not confirm:
        errors.append("Confirm password is required")
    if password and confirm and password != confirm:
        errors.append("Passwords do not match")
    return errors



@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("register.html", errors=[], form={})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    form = {"name": name, "email": email}

    errors = check_register(name, email, password, confirm)
    if errors:  # R8: show the page again, do not touch the database
        return render_template("register.html", errors=errors, form=form)

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, pw_hash),
            )
            new_id = cur.lastrowid
        db.commit()
    except pymysql.err.IntegrityError as e:
        db.rollback()
        if e.args[0] == 1062:  # duplicate e-mail (UNIQUE)
            return render_template("register.html", errors=["Email Already Exists"], form=form)
        raise

    session["user_id"] = new_id
    session["name"] = name
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("login.html", errors=[], form={})

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    form = {"email": email}

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if errors:
        return render_template("login.html", errors=errors, form=form)

    with get_db().cursor() as cur:
        cur.execute(
            "SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,)
        )
        user = cur.fetchone()

    ok = user is not None and bcrypt.checkpw(
        password.encode("utf-8"), user["password_hash"].encode("utf-8")
    )
    if not ok:  # same message for wrong e-mail and wrong password (R2)
        return render_template("login.html", errors=["Invalid email or password"], form=form)

    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))



def parse_due(raw):
    """BONUS: optional due date. Returns (date or None, list of errors)."""
    raw = (raw or "").strip()
    if not raw:
        return None, []
    try:
        return date.fromisoformat(raw), []
    except ValueError:
        return None, ["Due date is invalid"]


def build_list_query(flt, q):
    """BONUS: filter (all/open/done) + search. SQL pieces are fixed strings written here;
    the user's text only travels as a parameter."""
    sql = ("SELECT todo_id, title, is_done, created_at, due_date FROM todos "
           "WHERE user_id = %s")
    params = [session["user_id"]]
    if flt == "open":
        sql += " AND is_done = 0"
    elif flt == "done":
        sql += " AND is_done = 1"
    if q:
        safe = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND title LIKE %s"
        params.append("%" + safe + "%")
    sql += " ORDER BY todo_id DESC"
    return sql, params


def render_list(add_errors=None, add_title="", add_due="",
                edit_id=None, edit_errors=None, edit_title="", edit_due=""):
    current = session.get("filter", "all")
    q = session.get("q", "")
    sql, params = build_list_query(current, q)
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        todos = cur.fetchall()
        # BONUS: how many to-dos are still open
        cur.execute(
            "SELECT COUNT(*) AS open_count FROM todos WHERE user_id = %s AND is_done = 0",
            (session["user_id"],),
        )
        open_count = cur.fetchone()["open_count"]
    return render_template(
        "todos.html",
        todos=todos,
        name=session["name"],
        open_count=open_count,
        current=current,
        q=q,
        today=date.today(),
        add_errors=add_errors or [],
        add_title=add_title,
        add_due=add_due,
        edit_id=edit_id,
        edit_errors=edit_errors or [],
        edit_title=edit_title,
        edit_due=edit_due,
    )


@app.route("/")
@login_required
def index():
    # remember filter and search in the session so they survive add/edit/delete
    if request.args.get("filter") in ("all", "open", "done"):
        session["filter"] = request.args["filter"]
    if "q" in request.args:
        session["q"] = request.args["q"].strip()[:100]
    return render_list()


@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title", "").strip()
    due_raw = request.form.get("due_date", "")
    due, due_errors = parse_due(due_raw)
    errors = check_title(title) + due_errors
    if errors:
        return render_list(add_errors=errors, add_title=title, add_due=due_raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO todos (user_id, title, due_date) VALUES (%s, %s, %s)",
            (session["user_id"], title, due),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
@login_required
def edit(todo_id):
    title = request.form.get("title", "").strip()
    due_raw = request.form.get("due_date", "")
    due, due_errors = parse_due(due_raw)
    errors = check_title(title) + due_errors
    if errors:
        return render_list(edit_id=todo_id, edit_errors=errors,
                           edit_title=title, edit_due=due_raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET title = %s, due_date = %s WHERE todo_id = %s AND user_id = %s",
            (title, due, todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
@login_required
def toggle(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
            (is_done, todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
@login_required
def delete(todo_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
            (todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))



# LAB 3 - Library: authors and books (database `library`)

IMAGE_NAME = re.compile(r"^[0-9a-f]{32}\.(png|jpg|gif|webp)$")


def image_type(data):
    """BONUS: look at the first bytes of the file, not at its name."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def save_image(field):
    """BONUS: returns (new file name or None, errors). No file chosen = (None, [])."""
    f = request.files.get(field)
    if f is None or not f.filename:
        return None, []
    data = f.read()
    kind = image_type(data)
    if kind is None:
        return None, ["Image must be a PNG, JPG, GIF or WEBP file"]
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = uuid.uuid4().hex + "." + kind
    with open(os.path.join(UPLOAD_DIR, name), "wb") as out:
        out.write(data)
    return name, []


def delete_image(name):
    if name and IMAGE_NAME.match(name):  # only files this app created
        try:
            os.remove(os.path.join(UPLOAD_DIR, name))
        except OSError:
            pass


def check_author(name, country):
    errors = []
    if not name:
        errors.append("Name is required")
    elif len(name) > 100:
        errors.append("Name is too long (100 characters at most)")
    if not country:
        errors.append("Country is required")
    elif len(country) > 50:
        errors.append("Country is too long (50 characters at most)")
    return errors


def parse_price(raw):
    raw = (raw or "").strip()
    if not raw:
        return None, ["Price is required"]
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None, ["Price must be a number"]
    if not value.is_finite():
        return None, ["Price must be a number"]
    if value < 0:
        return None, ["Price cannot be negative"]
    if value.as_tuple().exponent < -2:
        return None, ["Price can have at most 2 decimal places"]
    if value > Decimal("99999999.99"):
        return None, ["Price is too large"]
    return value.quantize(Decimal("0.01")), []


def all_authors():
    with get_lib_db().cursor() as cur:
        cur.execute("SELECT author_id, name, country, photo FROM author ORDER BY author_id")
        return cur.fetchall()


def get_author(author_id):
    with get_lib_db().cursor() as cur:
        cur.execute("SELECT author_id, name, country, photo FROM author WHERE author_id = %s",
                    (author_id,))
        return cur.fetchone()


def get_book(book_id):
    with get_lib_db().cursor() as cur:
        cur.execute("SELECT book_id, title, price, author_id, cover FROM book WHERE book_id = %s",
                    (book_id,))
        return cur.fetchone()


@app.route("/library")
@login_required
def library():
    """F2.1: a table of the books (with author_id) and a table of the authors."""
    with get_lib_db().cursor() as cur:
        cur.execute("SELECT book_id, title, price, author_id, cover FROM book ORDER BY book_id")
        books = cur.fetchall()
    authors = all_authors()
    author_names = {a["author_id"]: a["name"] for a in authors}
    book_counts = {}
    for b in books:  # counted here, so no GROUP BY is needed
        book_counts[b["author_id"]] = book_counts.get(b["author_id"], 0) + 1
    return render_template("library.html", name=session["name"], books=books, authors=authors,
                           author_names=author_names, book_counts=book_counts)


# ---------- authors ----------
@app.route("/authors/add", methods=["GET", "POST"])
@login_required
def author_add():
    if request.method == "GET":
        return render_template("author_form.html", mode="add", errors=[], form={})
    name = request.form.get("name", "").strip()
    country = request.form.get("country", "").strip()
    form = {"name": name, "country": country}
    errors = check_author(name, country)
    photo, photo_errors = save_image("photo") if not errors else (None, [])
    errors += photo_errors
    if errors:
        return render_template("author_form.html", mode="add", errors=errors, form=form)
    db = get_lib_db()
    with db.cursor() as cur:
        cur.execute("INSERT INTO author (name, country, photo) VALUES (%s, %s, %s)",
                    (name, country, photo))
    db.commit()
    flash("Author added")
    return redirect(url_for("library"))


@app.route("/authors/<int:author_id>/edit", methods=["GET", "POST"])
@login_required
def author_edit(author_id):
    author = get_author(author_id)
    if author is None:
        abort(404)
    if request.method == "GET":
        return render_template("author_form.html", mode="edit", errors=[], form=author,
                               current_image=author["photo"])
    name = request.form.get("name", "").strip()
    country = request.form.get("country", "").strip()
    form = {"author_id": author_id, "name": name, "country": country}
    errors = check_author(name, country)
    new_photo, photo_errors = save_image("photo") if not errors else (None, [])
    errors += photo_errors
    if errors:
        return render_template("author_form.html", mode="edit", errors=errors, form=form,
                               current_image=author["photo"])
    db = get_lib_db()
    with db.cursor() as cur:
        cur.execute("UPDATE author SET name = %s, country = %s, photo = %s WHERE author_id = %s",
                    (name, country, new_photo or author["photo"], author_id))
    db.commit()
    if new_photo:
        delete_image(author["photo"])
    flash("Author updated")
    return redirect(url_for("library"))


@app.route("/authors/<int:author_id>/delete", methods=["POST"])
@login_required
def author_delete(author_id):
    """F2.5: the foreign key has ON DELETE CASCADE, so MySQL deletes the author's books too."""
    author = get_author(author_id)
    if author is None:
        abort(404)
    with get_lib_db().cursor() as cur:
        cur.execute("SELECT cover FROM book WHERE author_id = %s", (author_id,))
        covers = [row["cover"] for row in cur.fetchall()]
    db = get_lib_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM author WHERE author_id = %s", (author_id,))
    db.commit()
    delete_image(author["photo"])
    for cover in covers:
        delete_image(cover)
    flash("Author and their books deleted")
    return redirect(url_for("library"))


# ---------- books ----------
def read_book_form(authors):
    """Returns (form dict, price, errors) from the posted book form."""
    title = request.form.get("title", "").strip()
    price_raw = request.form.get("price", "").strip()
    author_raw = request.form.get("author_id", "").strip()
    errors = []
    if not title:
        errors.append("Title is required")
    elif len(title) > 200:
        errors.append("Title is too long (200 characters at most)")
    price, price_errors = parse_price(price_raw)
    errors += price_errors
    valid_ids = {str(a["author_id"]) for a in authors}
    if author_raw not in valid_ids:
        errors.append("Choose an author")
    form = {"title": title, "price": price_raw, "author_id": author_raw}
    return form, price, errors


@app.route("/books/add", methods=["GET", "POST"])
@login_required
def book_add():
    authors = all_authors()
    if request.method == "GET":
        return render_template("book_form.html", mode="add", errors=[], form={}, authors=authors)
    form, price, errors = read_book_form(authors)
    cover, cover_errors = save_image("cover") if not errors else (None, [])
    errors += cover_errors
    if errors:
        return render_template("book_form.html", mode="add", errors=errors, form=form,
                               authors=authors)
    db = get_lib_db()
    try:
        with db.cursor() as cur:
            cur.execute("INSERT INTO book (title, price, author_id, cover) VALUES (%s, %s, %s, %s)",
                        (form["title"], price, int(form["author_id"]), cover))
        db.commit()
    except pymysql.err.IntegrityError as e:
        db.rollback()
        delete_image(cover)
        if e.args[0] == 1452:  # the author was deleted a moment ago
            return render_template("book_form.html", mode="add", errors=["Choose an author"],
                                   form=form, authors=all_authors())
        raise
    flash("Book added")
    return redirect(url_for("library"))


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def book_edit(book_id):
    book = get_book(book_id)
    if book is None:
        abort(404)
    authors = all_authors()
    if request.method == "GET":
        form = {"book_id": book_id, "title": book["title"], "price": "%.2f" % book["price"],
                "author_id": str(book["author_id"])}
        return render_template("book_form.html", mode="edit", errors=[], form=form,
                               authors=authors, current_image=book["cover"])
    form, price, errors = read_book_form(authors)
    form["book_id"] = book_id
    new_cover, cover_errors = save_image("cover") if not errors else (None, [])
    errors += cover_errors
    if errors:
        return render_template("book_form.html", mode="edit", errors=errors, form=form,
                               authors=authors, current_image=book["cover"])
    db = get_lib_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE book SET title = %s, price = %s, author_id = %s, cover = %s "
                        "WHERE book_id = %s",
                        (form["title"], price, int(form["author_id"]),
                         new_cover or book["cover"], book_id))
        db.commit()
    except pymysql.err.IntegrityError as e:
        db.rollback()
        delete_image(new_cover)
        if e.args[0] == 1452:
            return render_template("book_form.html", mode="edit", errors=["Choose an author"],
                                   form=form, authors=all_authors(), current_image=book["cover"])
        raise
    if new_cover:
        delete_image(book["cover"])
    flash("Book updated")
    return redirect(url_for("library"))


@app.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
def book_delete(book_id):
    """F2.4"""
    book = get_book(book_id)
    if book is None:
        abort(404)
    db = get_lib_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
    db.commit()
    delete_image(book["cover"])
    flash("Book deleted")
    return redirect(url_for("library"))


@app.errorhandler(413)
def too_large(_e):
    return render_template("error.html", message="The image is too big (4 MB at most)"), 413


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", message="Page not found"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    app.run(debug=False)
