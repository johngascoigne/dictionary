import sqlite3
from sqlite3 import Error

from flask import Flask, render_template, request, redirect, session

from datetime import datetime

DB_NAME = "dictionary.db"

app = Flask(__name__)
app.secret_key = "banana"


def fetch_category_words(passed_category):
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description, added_by, timestamp, in_category FROM word WHERE in_category=?"

    cur = con.cursor()
    cur.execute(query, (passed_category,))
    word_query = cur.fetchall()

    con.close()
    fetched_words = []
    for i in word_query:
        x = int(i[4])
        x /= 1000
        fetched_words.append(
            [i[0], i[1], i[2], i[3], datetime.utcfromtimestamp(x).strftime('%Y-%m-%d at %H:%M:%S'), i[5]])

    con.close()
    return fetched_words


def fetch_authored_words(passed_user):
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description, added_by, timestamp, in_category FROM word WHERE added_by=?"

    cur = con.cursor()
    cur.execute(query, (passed_user,))
    word_query = cur.fetchall()

    con.close()
    fetched_words = []
    for i in word_query:
        x = int(i[4])
        x /= 1000
        fetched_words.append([i[0], i[1], i[2], i[3], datetime.utcfromtimestamp(x).strftime('%Y-%m-%d at %H:%M:%S'), i[5]])


    return fetched_words




def fetch_category_names():
    con = create_connection(DB_NAME)

    query = "SELECT name FROM category"

    cur = con.cursor()
    cur.execute(query)
    fetched_categories = cur.fetchall()

    lower_categories = []
    for i in range(len(fetched_categories)):
        j = fetched_categories[i]
        v = j[0]
        v = v.lower()
        lower_categories.append([v, v.title()])

    con.close()
    return lower_categories


def fetch_categories():
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description FROM category"

    cur = con.cursor()
    cur.execute(query)
    fetched_categories = cur.fetchall()

    con.close()
    return fetched_categories


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')
def render_homepage():
    return render_template('home.html', category_name=fetch_category_names(), logged_in=is_logged_in)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', category_name=fetch_category_names(), logged_in=is_logged_in)


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        if session.get('username') is not None:
            return redirect('/user/' + str(session.get('username')))
        else:
            return redirect('/login?error=Session+not+found')

    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = "SELECT id, username, password FROM user WHERE email = ?"
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            username = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect('/login?error=Email+or+password+incorrect')

        if db_password != password:
            return redirect('/login?error=Email+or+password+incorrect')

        session['email'] = email
        session['userid'] = userid
        session['username'] = username
        print(session)
        return redirect('/')
    return render_template('login.html', logged_in=is_logged_in(), categories=fetch_categories())


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == "POST":
        print(request.form)
        username = request.form.get('username').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password').strip()
        password2 = request.form.get('password2').strip()

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, username, email, password) VALUES(NULL,?,?,?,?)"

        cur = con.cursor()

        try:
            cur.execute(query, (username, email, password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+taken')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template('signup.html', category_name=fetch_category_names(), logged_in=is_logged_in)


@app.route('/category/<category>')
def render_category_page(category):
    return render_template('category.html', category_name=fetch_category_names(), cur_category=category,
                           category_words=fetch_category_words(category), logged_in=is_logged_in)


@app.route('/user/<username>')
def render_user_page(username):
    word_query = fetch_authored_words(username)
    authored_words = len(word_query)
    return render_template('user.html', category_name=fetch_category_names(), cur_user=username,
                           user_words=word_query, authored_word_count=authored_words,
                           logged_in=is_logged_in)


def is_logged_in():
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


app.run(host='0.0.0.0', debug=True)
