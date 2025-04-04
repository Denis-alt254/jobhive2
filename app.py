import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Deno8758@!'
app.config['MYSQL_DB'] = 'jobhive'

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, password):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(id=user[0], name=user[1], email=user[2], password=user[3])
    return None

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 3")
    jobs = cur.fetchall()
    cur.close()
    return render_template('index.html', jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        user_id = cur.lastrowid
        cur.close()

        user = User(id=user_id, name=name, email=email, password=password)
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            user_obj = User(id=user[0], name=user[1], email=user[2], password=user[3])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs WHERE posted_by = %s", (current_user.id,))
    jobs = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', jobs=jobs)

@app.route('/jobs')
def jobs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    cur.close()
    return render_template('jobs.html', jobs=jobs)

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        description = request.form['description']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO jobs (title, company, location, salary, description, posted_by) VALUES (%s, %s, %s, %s, %s, %s)",
                   (title, company, location, salary, description, current_user.id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/delete-job/<int:id>')
@login_required
def delete_job(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM jobs WHERE id = %s AND posted_by = %s", (id, current_user.id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)