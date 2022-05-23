import calendar
import sqlite3
from datetime import datetime
from sqlite3 import Error

from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt

DB_NAME = "dictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "banana"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


def remove(string):
    return string.replace(" ", "+")


def fetch_all_words():
    con = create_connection(DB_NAME)

    query = "SELECT * FROM word"

    cur = con.cursor()
    cur.execute(query, )
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


# fetch all words in a certain category
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


# fetch all words from a certain user
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
        fetched_words.append(
            [i[0], i[1], i[2], i[3], datetime.utcfromtimestamp(x).strftime('%Y-%m-%d at %H:%M:%S'), i[5]])

    return fetched_words


# fetch all names of categories and make them lowercase (for urls)
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

# get tha categories
def fetch_categories():
    con = create_connection(DB_NAME)

    query = "SELECT * FROM category"

    cur = con.cursor()
    cur.execute(query)
    fetched_categories = cur.fetchall()

    con.close()
    return fetched_categories


# fetch data from a category
def fetch_category_data(category_name):
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description FROM category"

    cur = con.cursor()
    cur.execute(query)
    fetched_categories = cur.fetchall()

    con.close()
    found_category = -1
    for i in range(len(fetched_categories)):
        x = fetched_categories[i][1]
        if x.lower() == category_name.lower():
            found_category = i
            break

    if found_category != -1:
        output_category = fetched_categories[found_category]
        return output_category

    else:
        return False


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')
def render_homepage():
    return render_template('home.html', category_name=fetch_category_names(), logged_in=is_logged_in())


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', category_name=fetch_category_names(), logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        if session.get('username') is not None:
            return redirect('/user/' + str(
                session.get('username')))  # redirects the user to their own userpage once they've logged in
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
    return render_template('login.html', category_name=fetch_category_names(), logged_in=is_logged_in(), )


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

    return render_template('signup.html', category_name=fetch_category_names(), logged_in=is_logged_in())


# main add page with radio buttons
@app.route('/add', methods=['GET', 'POST'])
def render_add_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == "POST":
        response = request.form['create']
        return redirect('/add/' + str(response))
    return render_template('add.html', category_name=fetch_category_names()
                           , logged_in=is_logged_in(), )


# redirects to this if u select the word radio button
@app.route('/add/word', methods=['GET', 'POST'])
def render_addword_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == "POST":
        username = session.get('username')

        print(request.form)
        word = request.form.get('word')
        desc = request.form.get('desc')
        category = request.form.get('category').lower()

        # now i have a dropdown menu, this code isn't necessary..

        # category_names = fetch_category_names()
        # print(category_names)
        # all_categories = []
        # for i in range(len(category_names)):
        #     all_categories.append(category_names[i][0])
        #
        # if category not in all_categories:
        #     return redirect('/addword?Category+does+not+exist')

        con = create_connection(DB_NAME)

        query = "INSERT INTO word(id, name, description, added_by, timestamp, in_category) VALUES(NULL,?,?,?,?,?)"

        cur = con.cursor()

        current_datetime = datetime.utcnow()
        current_timetuple = current_datetime.utctimetuple()
        current_timestamp = calendar.timegm(current_timetuple) * 1000
        try:
            cur.execute(query, (word, desc, username, current_timestamp, category))
        except ValueError:
            return redirect('/')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('addword.html', all_categories=fetch_categories(), category_name=fetch_category_names(),
                           logged_in=is_logged_in())


# and to this if you select category
@app.route('/add/category', methods=['GET', 'POST'])
def render_addcategory_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == "POST":
        print(request.form)
        name = request.form.get('name')
        desc = request.form.get('desc')

        con = create_connection(DB_NAME)

        query = "INSERT INTO category(id, name, description) VALUES(NULL,?,?)"

        cur = con.cursor()

        try:
            cur.execute(query, (name, desc))
        except ValueError:
            return redirect('/')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('addcategory.html', all_categories=fetch_categories(), category_name=fetch_category_names(),
                           logged_in=is_logged_in())


# unique category pages for all categories
@app.route('/category/<category>')
def render_category_page(category):
    return render_template('category.html', category_name=fetch_category_names(), cur_category=category,
                           category_words=fetch_category_words(category), logged_in=is_logged_in(),
                           category_data=fetch_category_data(category), )

# all words on one page :D
@app.route('/category/all')
def render_all_words_page():
    return render_template('allwords.html', category_name=fetch_category_names(), logged_in=is_logged_in(),
                           all_words=fetch_all_words(), )


#  unique user pages for all users
@app.route('/user/<username>')
def render_user_page(username):
    word_query = fetch_authored_words(username)  # get all authored words from the user
    authored_words = len(word_query)  # get the number of authored words (to be displayed on the user's page)
    return render_template('user.html', category_name=fetch_category_names(), cur_user=username,
                           user_words=word_query, authored_word_count=authored_words,
                           logged_in=is_logged_in(), )

@app.route('/remove_word/<word>')
def render_word_remove_page(word):

    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    con = create_connection(DB_NAME)

    query = "DELETE FROM word WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (word,))

    con.commit()

    query = "DELETE FROM word WHERE name=?"
    cur = con.cursor()

    cur.execute(query, (word,))
    con.commit()
    con.close()

    return redirect('/')

def is_logged_in():
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


app.run(host='0.0.0.0', debug=True)
