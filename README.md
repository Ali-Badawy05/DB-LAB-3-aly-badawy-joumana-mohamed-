# Lab 3: Foreign Keys and Simple SQL (Problem 2: Library)

Website from Lab 2 (login + to-do list), now with a **Library** section: books and authors in a second database called `library`.

## 1. Student
 Name | ID
1.aly badawy|2304123
2.joumana mohamed | 2304067

## 2. Technology
- Back end: Python 3 + Flask, PyMySQL (plain SQL with `%s` parameters, no ORM), bcrypt, python-dotenv
- Front end: HTML (Jinja templates), CSS, JavaScript (validation, delete confirmation, dark mode)
- Database: MySQL 8: `registration` (Lab 2: `users`, `todos`) and `library` (Lab 3: `author`, `book`)

## 3. Folder
```
problem2_DDL.sql   creates database `library`: tables author and book, with the foreign key
problem2_DML.sql   seed data: 4 authors, 8 books
website/           the Lab 2 website plus the new library pages
```

## 4. How to run it (Windows, step by step)
1. Install Python 3.10+ and MySQL 8.
2. Open **Command Prompt** (cmd) in this folder. In PowerShell the `<` symbol does not work; use cmd.
   If `mysql` is not found, use its full path, e.g. `"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"`.
3. Build the databases (each script can be re-run at any time):
   ```
   mysql -u root -p < problem2_DDL.sql
   mysql -u root -p < problem2_DML.sql
   mysql -u root -p < website\database\registration_schema.sql
   ```
4. Install the packages:
   ```
   cd website
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` (`copy .env.example .env`) and write your MySQL password and a random `SECRET_KEY`.
6. Start the server: `python app.py`
7. Open http://127.0.0.1:5000, **register** an account (the site is private, like Lab 2), then click **Library**.

(Linux / Mac: the same, with `source venv/bin/activate` and `cp .env.example .env`.)

## 5. Library pages
| Req. | Where |
|------|-------|
| F2.1 show the books (with `author_id`) and the authors | `/library` |
| F2.2 add a book / an author | `/books/add`, `/authors/add` |
| F2.3 edit a book / an author | `/books/<id>/edit`, `/authors/<id>/edit` |
| F2.4 remove a book | Delete button in the books table |
| F2.5 remove an author | Delete button in the authors table. The foreign key has `ON DELETE CASCADE`, so MySQL deletes the author's books too. The confirmation says how many books will go. |
| Bonus: images | Optional cover for a book and photo for an author (PNG, JPG, GIF, WEBP, 4 MB at most). The file is saved in `website/static/uploads/` and only its name is stored in the database (columns `book.cover` and `author.photo`, both NULL for the seed data). |

All checks run in the browser and again on the server. The price accepts at most 2 decimals and the author of a book must exist.
Only simple `SELECT / INSERT / UPDATE / DELETE` statements are used (no JOIN, no GROUP BY).

## 6. Lab 2 features (unchanged)
Register / login / logout, private to-do list, add, edit, done / not done, delete with confirmation, filter, search, due dates, dark mode.
