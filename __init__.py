from flask import Flask, render_template, flash, jsonify, request, url_for, \
                  redirect, session, g
from functools import wraps
from dbconnect import connection
from MySQLdb import escape_string
from wtforms import Form, TextField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt

import gc

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['username'] is None:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__)
app.config['SECRET_KEY'] = 'nuiv32orh8f34uifvnewivuh3924j3gp09'

@app.route('/')
def homepage():
    # session['username'] = None
    return render_template('main.html')




@app.route('/login/', methods=['GET', 'POST'])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == 'POST':
            data = c.execute('SELECT * FROM users WHERE username = ("%s");' %
                             escape_string(request.form['username']))
            print data
            data = c.fetchone()[2]  # Hashed password
            print data
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash('You are now logged in')
                return redirect(url_for('homepage'))
            else:
                error = 'Invalid credentials, try again'
        gc.collect()
        return render_template('login.html', error=error)

    except Exception as e:
        print e
        error = 'Invalid credentials, try again'
        return render_template('login.html', error=error)


@app.route('/logout/')
# @login_required
def logout_page():
    if session['logged_in']:
        session['logged_in'] = False
        session['username'] = None
    return redirect(url_for('homepage'))



class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email address', [validators.Length(min=5, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat password')
    accept_tos = BooleanField('I accept the <a href="/tos/">Terms of Service</a> and the <a href="/privacy/">Privacy Notice</a>.',
                              [validators.Required()])



@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    try:
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))

            c, conn = connection()
            x = c.execute('SELECT * FROM users WHERE username = ("%s")' %
                             escape_string(username))
            if int(x) > 0:
                flash('That username is already taken, please choose another')
                return render_template('register.html', form=form)
            else:
                c.execute('INSERT INTO users (username, password, email) VALUES ("%s", "%s", "%s")' %
                          (escape_string(username), escape_string(password), escape_string(email)))
                conn.commit()
                flash('Thanks for registering!')
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('homepage'))
        return render_template('register.html', form=form)

    except Exception as e:
        return str(e)



@app.route('/newrecipe/', methods=['GET', 'POST'])
def newrecipe():
    # flash('Uhh, give me a new recipe!')
    if request.method == 'POST':
        print request.form
    return render_template('newrecipe.html')


@app.route('/addrecipe/', methods=['POST', 'GET'])
def addrecipe():
    if request.method == 'POST':
        title = escape_string(request.form['title'])
        location = escape_string(request.form['country'])
        ingredients = escape_string(','.join(request.form['ingredients'].split('\r\n')).strip(','))
        recipe = escape_string(request.form['recipe'])
        # username = session['username']
        print title
        print location
        print ingredients
        print recipe
        c, conn = connection()

        c.execute('INSERT INTO recipes (title, location, ingredients, recipe) VALUES ("%s", "%s", "%s", "%s");' %
                                       (title, location, ingredients, recipe))
        conn.commit()  # Save to the database
        flash("Thanks for your recipe :)")
        c.close()
        conn.close()
        gc.collect()  # Garbage collection

        # return redirect(url_for('homepage'))
        return redirect(url_for('newrecipe'))
    else:
        return render_template('main.html')




@app.route('/_background/')
def background():
    try:
        i = request.args.get('ingredients_submit', 0, type=str)
        return jsonify(ingredient=i)
    except Error:
        return str(e)









if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
