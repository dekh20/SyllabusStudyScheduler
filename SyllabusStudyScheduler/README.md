# Syllab.Us : Syllabus Study Scheduler
Condense all course syllabi, determine conflicting deadlines, and schedule study times based on individual's learning styles.

## Run locally

No extra libraries are needed for the website. Python 3.10+.

```
python app.py        # Windows: py app.py
```

Open http://127.0.0.1:8000. Press Ctrl+C in the terminal to stop. Accounts and assignments are saved in `syllabus_demo.sqlite3` (delete it to start fresh).

Run the tests (needs `pip install pytest`):

```
python -m pytest     # Windows: py -m pytest
```

## Project layout

- `app.py` — local web server: handles requests and fills in the HTML pages
- `core.py` — accounts, assignments, reminders (SQLite)
- `frontend/` — the website's HTML pages and `style.css`
  - `base.html` page shell (top bar, footer) · `login.html` sign in / create account · `dashboard.html` student dashboard
  - `task_row.html`, `reminder.html` repeated pieces of the dashboard · `message.html` short message pages
- `py_unit_test_code/` — team classes from earlier labs and their unit tests
- `test_core.py` — tests for `core.py`
