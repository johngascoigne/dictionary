import calendar
import sqlite3
from datetime import datetime
from sqlite3 import Error

import pytz
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt

DB_NAME = 'dictionary.db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = '(&*SDya87dsya8dghP}_yadhsayAS*&dt&*^d%^&DS$AdasdtfiyguvasdvaG!Y#GUY@^%@R#^%&R%@^#rgj'

timezone = pytz.timezone('Pacific/Auckland')


# converts the timestamp to a utc timestamp.
# also will append all of the word data to a list.
def timestamp_and_data(active_list, target_list):
    for i in active_list:
        x = int(i[5])
        x /= 1000
        # i had to use pytz for the timestamp, as datetime would return the wrong time (off by 12 hrs)
        timestamp = datetime.fromtimestamp(x, timezone)

        timestamp_str = str(timestamp)  # need it to be a string!

        timestamp_fh = timestamp_str[
                       0:len(timestamp_str) - 15]  # cuts off the hr, min, sec so i can add 'at' between date and time

        timestamp_lh = timestamp_str[11:len(timestamp_str) - 6]  # cuts off '+12'

        timestamp = timestamp_fh + ' at ' + timestamp_lh

        target_list.append(
            [i[0], i[1], i[2], i[3], i[4], timestamp, i[6], i[7], i[8]])

# convert word's in_category id to an id and name from category table
def id_to_category(word):
    con = create_connection(DB_NAME)

    query = 'SELECT in_category FROM word WHERE id=?'

    cur = con.cursor()
    cur.execute(query, (word,))
    fetched_id = cur.fetchall()
    con.close()

    fetched_id = fetched_id[0][0]

    con = create_connection(DB_NAME)

    query = 'SELECT id, name FROM category WHERE id=?'

    cur = con.cursor()
    cur.execute(query, (fetched_id,))
    fetched_data = cur.fetchall()

    con.close()
    return fetched_data[0][1]


# create the connection
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


# fetches all words ( for category: allwords )
def fetch_all_words():
    con = create_connection(DB_NAME)

    query = 'SELECT id, english, maori, description, added_by, timestamp, in_category, image, wordlevel FROM word'

    cur = con.cursor()
    cur.execute(query, )

    word_query = cur.fetchall()
    con.close()

    fetched_words = []
    timestamp_and_data(word_query, fetched_words)

    con.close()
    return fetched_words


# fetch all words in a certain category
def fetch_category_words(passed_category):
    con = create_connection(DB_NAME)

    query = 'SELECT id FROM category WHERE id=?'

    cur = con.cursor()

    cur.execute(query, (passed_category,))
    found_category_id = cur.fetchall()

    found_category_id = found_category_id[0][0]

    query = 'SELECT id, english, maori, description, added_by, timestamp, in_category, image, wordlevel FROM word ' \
            'WHERE in_category=?'

    cur = con.cursor()

    cur.execute(query, (found_category_id,))

    word_query = cur.fetchall()

    con.close()

    fetched_words = []

    timestamp_and_data(word_query, fetched_words)

    con.close()
    return fetched_words


# fetch all words from a certain user
def fetch_authored_words(passed_user):
    con = create_connection(DB_NAME)

    query = 'SELECT id, english, maori, description, added_by, timestamp, in_category, image, wordlevel FROM word ' \
            'WHERE added_by=?'

    cur = con.cursor()
    cur.execute(query, (passed_user,))
    word_query = cur.fetchall()

    con.close()
    fetched_words = []
    timestamp_and_data(word_query, fetched_words)

    return fetched_words


# fetch all categories
def fetch_categories():
    con = create_connection(DB_NAME)

    query = 'SELECT * FROM category'

    cur = con.cursor()
    cur.execute(query)
    fetched_categories = cur.fetchall()

    con.close()
    return fetched_categories


# fetch data from a specific category
def fetch_category_data(category_id):
    con = create_connection(DB_NAME)

    query = 'SELECT id, name, description FROM category WHERE id=?'

    cur = con.cursor()
    cur.execute(query, (category_id,))
    fetched_categories = cur.fetchall()

    con.close()
    return fetched_categories

# fetches the general word data from a specific word of id #
def fetch_word_data(word):
    con = create_connection(DB_NAME)

    query = 'SELECT id, english, maori, description, added_by, timestamp, in_category, image, wordlevel FROM word ' \
            'WHERE id=?'

    cur = con.cursor()
    cur.execute(query, (word,))
    fetched_word = cur.fetchall()

    word_data = []

    timestamp_and_data(fetched_word, word_data)

    con.close()
    return word_data


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None

# homepage
@app.route('/')
def render_homepage():
    username = session.get('username')
    return render_template('home.html', categories=fetch_categories(), logged_in=is_logged_in(), admin=is_admin(),
                           cur_user=username, )

# contact page
@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', categories=fetch_categories(), logged_in=is_logged_in(), admin=is_admin())

# login page
@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        if session.get('username') is not None:
            return redirect('/user/' + str(
                session.get('username')))  # redirects the user to their own userpage once they've logged in
        else:
            return redirect('/login?error=Session+not+found')

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = 'SELECT id, username, password, is_admin FROM user WHERE email =?'
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            username = user_data[0][1]
            db_password = user_data[0][2]
            admin = user_data[0][3]
        except IndexError:
            return redirect('/login?error=Email+or+password+incorrect')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + '?error=Email+or+password+incorrect')

        session['email'] = email
        session['userid'] = userid
        session['username'] = username
        session['admin'] = admin
        print(session)
        return redirect('/')
    return render_template('login.html', categories=fetch_categories(), logged_in=is_logged_in(), )

# signup page
@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == 'POST':
        print(request.form)
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password').strip()
        password2 = request.form.get('password2').strip()
        admin = request.form.get('admin')

        if admin:
            admin = 1
        elif not admin:
            admin = 0

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        # generate a hashed password from entered password
        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = 'INSERT INTO user(id, username, email, password, is_admin) VALUES(NULL,?,?,?,?)'

        cur = con.cursor()

        try:
            cur.execute(query, (username, email, hashed_password, admin))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+taken')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template('signup.html', categories=fetch_categories(), logged_in=is_logged_in(), )


# main add page with radio buttons
@app.route('/add', methods=['GET', 'POST'])
def render_add_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == 'POST':
        response = request.form['create']
        return redirect('/add/' + str(response))
    return render_template('add.html', categories=fetch_categories(), logged_in=is_logged_in(), admin=is_admin())


# redirects to this if u select the word radio button
@app.route('/add/word', methods=['GET', 'POST'])
def render_addword_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == 'POST':
        username = session.get('username')

        english = request.form.get('english')
        maori = request.form.get('maori')
        desc = request.form.get('desc')
        category = request.form.get('category').lower()
        wordlevel = request.form.get('wordlevel')

        con = create_connection(DB_NAME)

        query = 'INSERT INTO word(id, english, maori, description, added_by, timestamp, in_category,' \
                ' wordlevel, image) VALUES(NULL,?,?,?,?,?,?,?,?)'

        cur = con.cursor()

        current_datetime = datetime.utcnow()
        current_timetuple = current_datetime.utctimetuple()
        current_timestamp = calendar.timegm(current_timetuple) * 1000
        try:
            cur.execute(query, (english, maori, desc, username, current_timestamp, category, wordlevel, 'noimage.png'))
        except ValueError:
            return redirect('/')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('addword.html', categories=fetch_categories(),
                           logged_in=is_logged_in(), admin=is_admin())


# and to this if you select category
@app.route('/add/category', methods=['GET', 'POST'])
def render_addcategory_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if request.method == 'POST':
        print(request.form)
        name = request.form.get('name')
        desc = request.form.get('desc')

        con = create_connection(DB_NAME)

        query = 'INSERT INTO category(id, name, description) VALUES(NULL,?,?)'

        cur = con.cursor()

        try:
            cur.execute(query, (name, desc))
        except ValueError:
            return redirect('/')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('addcategory.html', categories=fetch_categories(),
                           logged_in=is_logged_in(), admin=is_admin())


# unique category pages for all categories
@app.route('/category/<category>')
def render_category_page(category):
    con = create_connection(DB_NAME)

    query = 'SELECT id FROM category where id=?'

    cur = con.cursor()
    cur.execute(query, (category,))

    category_query = cur.fetchall()
    con.close()

    print(category_query)

    if not category_query:
        return redirect('/?error=Category+does+not+exist')
    return render_template('category.html', categories=fetch_categories(), cur_category=category,
                           category_words=fetch_category_words(category), logged_in=is_logged_in(),
                           category_data=fetch_category_data(category), admin=is_admin())


# unique category pages for all categories
@app.route('/word/<word>')
def render_word_page(word):
    con = create_connection(DB_NAME)

    query = 'SELECT id FROM word where id=?'

    cur = con.cursor()
    cur.execute(query, (word,))

    word_query = cur.fetchall()
    con.close()

    print(word_query)

    if not word_query:
        return redirect('/?error=Word+does+not+exist')

    return render_template('word.html', categories=fetch_categories(), cur_category=word, logged_in=is_logged_in(),
                           admin=is_admin(), word_data=fetch_word_data(word), category_name=id_to_category(word))


# all words on one page :D
@app.route('/category/all')
def render_all_words_page():
    return render_template('allwords.html', categories=fetch_categories(), logged_in=is_logged_in(),
                           all_words=fetch_all_words(), admin=is_admin())


#  unique user pages for all users
@app.route('/user/<username>')
def render_user_page(username):
    con = create_connection(DB_NAME)

    query = 'SELECT id FROM user WHERE username=?'

    cur = con.cursor()
    cur.execute(query, (username,))

    user_query = cur.fetchall()
    con.close()

    if not user_query:
        return redirect('/?error=User+does+not+exist')

    word_query = fetch_authored_words(username)  # get all authored words from the user

    authored_words = len(word_query)  # get the number of authored words (to be displayed on the user's page)
    return render_template('user.html', categories=fetch_categories(), cur_user=username,
                           user_words=word_query, authored_word_count=authored_words,
                           logged_in=is_logged_in(), admin=is_admin(), )

# for removing words of specific id #'s
@app.route('/remove_word/<word>')
def render_word_remove_page(word):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    con = create_connection(DB_NAME)

    query = 'DELETE FROM word WHERE id=?'
    cur = con.cursor()

    cur.execute(query, (word,))

    con.commit()

    return redirect('/')

# logout
@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=Goodbye!')

# to check if the user is logged in
def is_logged_in():
    if session.get('email') is None:
        print('Not logged in')
        return False
    else:
        print('Logged in')
        return True

# to check if the account the user has logged in with is an admin
def is_admin():
    if is_logged_in() and session.get('admin') == 1:
        return True

    else:
        return False


app.run(host='0.0.0.0', debug=True)
