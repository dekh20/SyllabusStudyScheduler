"""Run with: python3 app.py; open http://127.0.0.1:8000

Local educational prototype. No external libraries required.
"""
from html import escape
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import os
import secrets

from core import Database, reminder_items

PORT = int(os.environ.get('SYLLABUS_PORT', '8000'))
DB = Database(Path(__file__).with_name('syllabus_demo.sqlite3'))
SESSIONS = {}  # local demo: token -> {user_id, csrf}

CSS = '''
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#192c3d;background:#f5f8fa}*{box-sizing:border-box}body{margin:0}
a{color:#18766a;text-decoration:none}h1,h2,h3,p{margin-top:0}.wrap{max-width:1060px;margin:0 auto;padding:28px 24px}
nav{background:#fff;border-bottom:1px solid #e1e8ed}.navin{display:flex;align-items:center;justify-content:space-between;gap:15px;max-width:1060px;margin:auto;padding:17px 24px}
.brand{font-size:22px;font-weight:850;letter-spacing:-1px;color:#183a3a}.brand em{font-style:normal;color:#0a9882}
nav form{display:inline}.muted{color:#627581}.eyebrow{color:#087f70;font-size:12px;letter-spacing:1.4px;font-weight:800;text-transform:uppercase}
h1{font-size:34px;line-height:1.15;letter-spacing:-1.2px;margin-bottom:10px}.lead{font-size:16px;line-height:1.6;max-width:720px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.card{background:#fff;border:1px solid #dde6eb;border-radius:17px;padding:25px;box-shadow:0 7px 26px #1f425009}
.card h2{font-size:19px}.card h3{font-size:15px}label{display:block;font-size:13px;font-weight:750;margin:14px 0 7px}
input,select{font:inherit;width:100%;padding:12px 13px;border:1px solid #c9d8df;border-radius:9px;background:white;color:#193042}
input:focus,select:focus{outline:3px solid #a4e9dc;border-color:#0d9488}
button,.btn{display:inline-flex;align-items:center;justify-content:center;background:#087f70;color:white;border:0;border-radius:9px;padding:11px 16px;font:inherit;font-size:14px;font-weight:750;cursor:pointer}
button:hover,.btn:hover{background:#076458;color:white}.secondary{background:#edf4f4;color:#215751}.secondary:hover{background:#dcebe9;color:#215751}
.small{font-size:12px}.inline{display:inline}.notice{border-radius:10px;padding:12px 15px;margin:18px 0;background:#e9f8f2;border:1px solid #a3e4c5;color:#126148}
.error{background:#fff0ef;border-color:#ffbbb6;color:#a6332d}.sectionhead{display:flex;align-items:center;justify-content:space-between;gap:12px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:25px 0}.stat{border-radius:13px;background:#fff;border:1px solid #dfe9ec;padding:17px}.stat strong{display:block;font-size:26px;letter-spacing:-1px}.stat span{font-size:12px;color:#71818d}
.task{padding:15px 0;border-bottom:1px solid #e7eef1}.task:last-child{border-bottom:0}.tasktop{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.taskname{font-weight:800}.tag{display:inline-block;padding:4px 9px;background:#e8f7f3;border-radius:100px;color:#087c6b;font-size:12px;font-weight:750}
.taskcontrols{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:11px}.taskcontrols select{width:auto;min-width:155px;padding:7px}.taskcontrols button{padding:8px 10px}
.alert{background:#fff9eb;border:1px solid #f3d6a0;border-radius:12px;padding:12px 14px;margin:10px 0}.alert strong{display:block}
.hero{padding:35px 0 20px}.footer{color:#8596a1;font-size:12px;margin-top:30px;text-align:center}
@media(max-width:760px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr 1fr}.wrap{padding:22px 15px}h1{font-size:27px}.card{padding:18px}}
'''


def q(value):
    return escape(str(value), quote=True)


def page(content, name=None, notice='', error=''):
    account = f'<span class="muted small">Signed in as {q(name)}</span>' if name else '<span class="muted small">Lab 7 prototype</span>'
    notes = (f'<div role="status" class="notice">{q(notice)}</div>' if notice else '') + (f'<div role="alert" class="notice error">{q(error)}</div>' if error else '')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Syllab.Us — Login & Tasks</title><style>{CSS}</style></head><body>
<nav><div class="navin"><a class="brand" href="/">Syllab<em>.Us</em></a>{account}</div></nav><main class="wrap">{notes}{content}<p class="footer">CSEN 174 · Lab 7 prototype · Local development only · Login, assignment progress & in-app reminders</p></main></body></html>'''


def auth_page():
    return page('''<div class="hero"><p class="eyebrow">Your academic command center</p><h1>Less deadline stress. More progress.</h1><p class="lead muted">Create a student account, sign in securely, track assignments, and see reminders for work due within the next 48 hours.</p></div>
<div class="grid"><section class="card"><h2>Welcome back</h2><p class="muted small">Enter your email and password to access your dashboard.</p><form method="post" action="/login">
<label for="login-email">School email</label><input id="login-email" name="email" type="email" autocomplete="username" required>
<label for="login-password">Password</label><input id="login-password" name="password" type="password" autocomplete="current-password" required>
<p></p><button type="submit">Sign in</button></form></section>
<section class="card"><h2>New to Syllab.Us?</h2><p class="muted small">Create an account for the prototype. Accounts and assignments are saved locally.</p><form method="post" action="/register">
<label for="register-name">Full name</label><input id="register-name" name="name" autocomplete="name" maxlength="80" required>
<label for="register-email">Email address</label><input id="register-email" name="email" type="email" autocomplete="email" required>
<label for="register-password">Password (8+ characters)</label><input id="register-password" name="password" type="password" autocomplete="new-password" minlength="8" required>
<p></p><button class="secondary" type="submit">Create account</button></form></section></div>''')



def dashboard(student, tasks, csrf):
    pending = sum(task['status'] != 'completed' for task in tasks)
    completed = len(tasks)-pending
    reminders = reminder_items(tasks)
    rows = []
    for task in tasks:
        state = {'not_started':'Not started', 'in_progress':'In progress', 'completed':'Completed'}[task['status']]
        choices = ''.join(f'<option value="{st}" {"selected" if st==task["status"] else ""}>{label}</option>' for st,label in [('not_started','Not started'),('in_progress','In progress'),('completed','Completed')])
        rows.append(f'''<div class="task"><div class="tasktop"><div><div class="taskname">{q(task['title'])}</div><div class="muted small">{q(task['course'])} · Due {q(task['due_at'].replace('T',' at '))}</div></div><span class="tag">{q(state)}</span></div>
        <div class="taskcontrols"><form class="taskcontrols" method="post" action="/status"><input type="hidden" name="csrf" value="{q(csrf)}"><input type="hidden" name="id" value="{task['id']}"><select name="status" aria-label="Progress for {q(task['title'])}">{choices}</select><button class="secondary">Save status</button></form>
        <form method="post" action="/delete"><input type="hidden" name="csrf" value="{q(csrf)}"><input type="hidden" name="id" value="{task['id']}"><button type="submit" class="secondary">Delete</button></form></div></div>''')
    reminder_html = ''.join(f'<div class="alert"><strong>{q(t["title"])}</strong><span class="small">{q(t["course"])} · Due {q(t["due_at"].replace("T"," at "))}</span></div>' for t in reminders) if reminders else '<p class="muted small">Nothing due in the next 48 hours. Nice work!</p>'
    return page(f'''<div class="hero sectionhead"><div><p class="eyebrow">Student dashboard</p><h1>Welcome, {q(student['name'].split()[0])}.</h1><p class="lead muted">Keep your courses organized and stay ahead of upcoming deadlines.</p></div><form method="post" action="/logout"><input type="hidden" name="csrf" value="{q(csrf)}"><button class="secondary">Log out</button></form></div>
    <div class="stats"><div class="stat"><strong>{len(tasks)}</strong><span>Total tasks</span></div><div class="stat"><strong>{pending}</strong><span>To do</span></div><div class="stat"><strong>{completed}</strong><span>Completed</span></div></div>
    <div class="grid"><section class="card"><h2>Add an assignment</h2><form method="post" action="/add"><input type="hidden" name="csrf" value="{q(csrf)}"><label for="task-title">Assignment title</label><input name="title" id="task-title" placeholder="e.g. Software Engineering Lab 7" required maxlength="150"><label for="task-course">Course</label><input name="course" id="task-course" placeholder="e.g. CSEN 174" required maxlength="80"><label for="task-due">Due date and time</label><input id="task-due" type="datetime-local" name="due_at" required><p></p><button>Add assignment</button></form></section>
    <section class="card"><div class="sectionhead"><h2>Upcoming reminders</h2><span class="tag">48-hour window</span></div><p class="muted small">Shows unfinished assignments due within 48 hours. Refreshing the dashboard updates this list.</p>{reminder_html}</section></div>
    <section class="card" style="margin-top:22px"><div class="sectionhead"><h2>My assignments</h2><span class="muted small">{len(tasks)} total</span></div>{''.join(rows) if rows else '<p class="muted">No assignments yet. Add your first one above.</p>'}</section>''', student['name'])


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

    def send_html(self, html, status=200, cookie=None, clear=False):
        raw = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', f'syllabus_session={cookie}; HttpOnly; SameSite=Lax; Path=/')
        if clear:
            self.send_header('Set-Cookie', 'syllabus_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
        self.end_headers()
        self.wfile.write(raw)

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
        if self.path != '/':
            self.send_html(page('<h1>Page not found</h1>'), status=404)
            return
        session = self.session()
        if session:
            student = DB.get_student(session['user_id'])
            if student:
                self.send_html(dashboard(student, DB.list_tasks(student['id']), session['csrf']))
                return
        self.send_html(auth_page())

    def form(self):
        size = int(self.headers.get('Content-Length','0'))
        if size > 16_384:
            raise ValueError('Form input is too large.')
        encoded = self.rfile.read(size).decode('utf-8')
        return {k: values[0] for k,values in parse_qs(encoded,keep_blank_values=True).items()}

    def do_POST(self):
        try:
            form = self.form()
            action = self.path
            if action == '/register':
                DB.create_student(form.get('name',''),form.get('email',''),form.get('password',''))
                self.send_html(page('<h1>Account created</h1><p>Your account is ready. Return to the login screen.</p><a class="btn" href="/">Sign in</a>'))
                return
            if action == '/login':
                student = DB.authenticate(form.get('email'), form.get('password'))
                if not student:
                    self.send_html(page('<h1>Sign-in unsuccessful</h1><p>Incorrect email or password.</p><a class="btn" href="/">Try again</a>'),status=401)
                    return
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = {'user_id': student['id'], 'csrf': secrets.token_urlsafe(32)}
                self.redirect('/', cookie=token)
                return
            session = self.session()
            if not session:
                self.redirect('/')
                return
            if not secrets.compare_digest(session['csrf'],form.get('csrf','')):
                self.send_html(page('<h1>Request rejected</h1><p>Invalid form token.</p>'),status=403)
                return
            user_id = session['user_id']
            if action == '/add':
                DB.add_task(user_id,form.get('title',''),form.get('course',''),form.get('due_at',''))
            elif action == '/status':
                DB.update_status(user_id,int(form.get('id','0')),form.get('status',''))
            elif action == '/delete':
                DB.delete_task(user_id,int(form.get('id','0')))
            elif action == '/logout':
                SESSIONS.pop(self.cookie(),None)
                self.redirect('/',clear=True)
                return
            else:
                self.send_html(page('<h1>Page not found</h1>'),status=404)
                return
            self.redirect('/')
        except (ValueError,TypeError) as exc:
            self.send_html(page('<h1>Check your input</h1><p>'+q(exc)+'</p><a class="btn" href="/">Go back</a>'),status=400)


def run():
    server = ThreadingHTTPServer(('127.0.0.1', PORT),AppHandler)
    print(f'Syllab.Us Lab 7 running: http://127.0.0.1:{PORT}')
    print('Press Control+C to stop. Data is saved in syllabus_demo.sqlite3')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    run()
