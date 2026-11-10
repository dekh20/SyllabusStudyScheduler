"""Run with: python app.py  (Windows: py app.py), then open http://127.0.0.1:8000

Syllab.Us local prototype. No external libraries required.
The pages are plain HTML files in frontend/ and the styles are in frontend/style.css.
This file only handles requests and fills the ${...} placeholders in those files.
"""
from html import escape
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs
import os
import secrets

from core import Database, reminder_items

PORT = int(os.environ.get('SYLLABUS_PORT', '8000'))
DB = Database(Path(__file__).with_name('syllabus_demo.sqlite3'))
SESSIONS = {}  # local demo: token -> {user_id, csrf}
FRONTEND = Path(__file__).with_name('frontend')

# Files the browser may download directly: URL path -> (file in frontend/, content type)
STATIC_FILES = {
    '/static/style.css': ('style.css', 'text/css; charset=utf-8'),
}

STATUS_LABELS = [('not_started', 'Not started'), ('in_progress', 'In progress'), ('completed', 'Completed')]


def q(value):
    """Escape text before putting it into HTML."""
    return escape(str(value), quote=True)


def render(name, **values):
    """Read frontend/<name> and fill in its ${...} placeholders.

    Files are read on every request, so edits to the HTML show up on refresh.
    Every value passed here must already be safe HTML (escape user text with q()).
    """
    text = (FRONTEND / name).read_text(encoding='utf-8')
    return Template(text).substitute(values)


def page(content, name=None, notice='', error=''):
    account = (f'<span class="muted small">Signed in as {q(name)}</span>' if name
               else '<span class="muted small">Syllab.Us prototype</span>')
    notes = ((f'<div role="status" class="notice">{q(notice)}</div>' if notice else '')
             + (f'<div role="alert" class="notice error">{q(error)}</div>' if error else ''))
    return render('base.html', account=account, notices=notes, content=content)


def message_page(heading, message='', button_text='', button_href='/'):
    button = f'<a class="btn" href="{q(button_href)}">{q(button_text)}</a>' if button_text else ''
    return page(render('message.html', heading=q(heading), message=q(message), button=button))


def auth_page():
    return page(render('login.html'))


def dashboard(student, tasks, csrf):
    pending = sum(task['status'] != 'completed' for task in tasks)
    completed = len(tasks) - pending

    rows = []
    for task in tasks:
        state = dict(STATUS_LABELS)[task['status']]
        options = ''.join(
            f'<option value="{value}" {"selected" if value == task["status"] else ""}>{label}</option>'
            for value, label in STATUS_LABELS)
        rows.append(render('task_row.html', title=q(task['title']), course=q(task['course']),
                           due=q(task['due_at'].replace('T', ' at ')), state=q(state),
                           csrf=q(csrf), id=q(task['id']), status_options=options))

    reminders = reminder_items(tasks)
    reminder_html = (''.join(render('reminder.html', title=q(t['title']), course=q(t['course']),
                                    due=q(t['due_at'].replace('T', ' at ')))
                             for t in reminders)
                     if reminders else '<p class="muted small">Nothing due in the next 48 hours. Nice work!</p>')

    content = render('dashboard.html', first_name=q(student['name'].split()[0]), csrf=q(csrf),
                     total=len(tasks), pending=pending, completed=completed,
                     reminders=reminder_html,
                     task_rows=''.join(rows) if rows else '<p class="muted">No assignments yet. Add your first one above.</p>')
    return page(content, student['name'])


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('[local demo]', fmt % args)

    def cookie(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
            return cookies['syllabus_session'].value if 'syllabus_session' in cookies else None
        except Exception:
            return None

    def send_bytes(self, raw, content_type, status=200, cookie=None, clear=False):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', f'syllabus_session={cookie}; HttpOnly; SameSite=Lax; Path=/')
        if clear:
            self.send_header('Set-Cookie', 'syllabus_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
        self.end_headers()
        self.wfile.write(raw)

    def send_html(self, html, status=200, cookie=None, clear=False):
        self.send_bytes(html.encode('utf-8'), 'text/html; charset=utf-8', status, cookie, clear)

    def redirect(self, path, cookie=None, clear=False):
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header('Location', path)
        if cookie:
            self.send_header('Set-Cookie', f'syllabus_session={cookie}; HttpOnly; SameSite=Lax; Path=/')
        if clear:
            self.send_header('Set-Cookie', 'syllabus_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
        self.end_headers()

    def session(self):
        return SESSIONS.get(self.cookie())

    def do_GET(self):
        if self.path in STATIC_FILES:
            filename, content_type = STATIC_FILES[self.path]
            self.send_bytes((FRONTEND / filename).read_bytes(), content_type)
            return
        if self.path != '/':
            self.send_html(message_page('Page not found'), status=404)
            return
        session = self.session()
        if session:
            student = DB.get_student(session['user_id'])
            if student:
                self.send_html(dashboard(student, DB.list_tasks(student['id']), session['csrf']))
                return
        self.send_html(auth_page())

    def form(self):
        size = int(self.headers.get('Content-Length', '0'))
        if size > 16_384:
            raise ValueError('Form input is too large.')
        encoded = self.rfile.read(size).decode('utf-8')
        return {k: values[0] for k, values in parse_qs(encoded, keep_blank_values=True).items()}

    def do_POST(self):
        try:
            form = self.form()
            action = self.path
            if action == '/register':
                DB.create_student(form.get('name', ''), form.get('email', ''), form.get('password', ''))
                self.send_html(message_page('Account created',
                                            'Your account is ready. Return to the login screen.', 'Sign in'))
                return
            if action == '/login':
                student = DB.authenticate(form.get('email'), form.get('password'))
                if not student:
                    self.send_html(message_page('Sign-in unsuccessful', 'Incorrect email or password.',
                                                'Try again'), status=401)
                    return
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = {'user_id': student['id'], 'csrf': secrets.token_urlsafe(32)}
                self.redirect('/', cookie=token)
                return
            session = self.session()
            if not session:
                self.redirect('/')
                return
            if not secrets.compare_digest(session['csrf'], form.get('csrf', '')):
                self.send_html(message_page('Request rejected', 'Invalid form token.'), status=403)
                return
            user_id = session['user_id']
            if action == '/add':
                DB.add_task(user_id, form.get('title', ''), form.get('course', ''), form.get('due_at', ''))
            elif action == '/status':
                DB.update_status(user_id, int(form.get('id', '0')), form.get('status', ''))
            elif action == '/delete':
                DB.delete_task(user_id, int(form.get('id', '0')))
            elif action == '/logout':
                SESSIONS.pop(self.cookie(), None)
                self.redirect('/', clear=True)
                return
            else:
                self.send_html(message_page('Page not found'), status=404)
                return
            self.redirect('/')
        except (ValueError, TypeError) as exc:
            self.send_html(message_page('Check your input', str(exc), 'Go back'), status=400)


def run():
    server = ThreadingHTTPServer(('127.0.0.1', PORT), AppHandler)
    print(f'Syllab.Us running: http://127.0.0.1:{PORT}')
    print('Press Control+C to stop. Data is saved in syllabus_demo.sqlite3')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    run()
