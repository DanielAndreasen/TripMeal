from flask import Flask, render_template, flash, jsonify, request, url_for, \
                  redirect, session, g
from dbconnect import connection
from MySQLdb import escape_string
from wtforms import Form, TextField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import gc


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email address', [validators.Length(min=5, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat password')
    accept_tos = BooleanField('I accept the <a href="/tos/">Terms of Service</a> and the <a href="/privacy/">Privacy Notice</a>.',
                              [validators.Required()])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['username'] is None:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nuiv32orh8f34uifvnewivuh3924j3gp09'


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route('/login/', methods=['GET', 'POST'])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == 'POST':
            data = c.execute('SELECT * FROM users WHERE username = ("%s");' %
                             escape_string(request.form['username']))
            data = c.fetchone()
            if sha256_crypt.verify(request.form['password'], data[2]):
                session['logged_in'] = True
                session['username'] = request.form['username']
                session['favourites'] = data[4]
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
@login_required
def logout_page():
    if session['logged_in']:
        session['logged_in'] = False
        session['username'] = None
    return redirect(url_for('homepage'))


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
@login_required
def newrecipe():
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
        username = session['username']
        c, conn = connection()

        c.execute('INSERT INTO recipes (title, location, ingredients, recipe, user) VALUES ("%s", "%s", "%s", "%s", "%s");' %
                                       (title, location, ingredients, recipe, username))
        conn.commit()  # Save to the database
        flash("Thanks for your recipe :)")
        c.close()
        conn.close()
        gc.collect()  # Garbage collection

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


@app.route('/recipes/')
def list_recipes():
    c, conn = connection()
    _ = c.execute('SELECT rid, title FROM recipes;')
    recipes = c.fetchall()
    c.close()
    conn.close()
    gc.collect()

    return render_template('recipes.html', recipes=recipes)


@app.route('/recipe/', methods=['POST', 'GET'])
def list_recipe():
    try:
        if request.method == 'GET':
            rid = request.args.get('rid')
            c, conn = connection()
            _ = c.execute('SELECT * FROM recipes WHERE rid = %s' % escape_string(rid))
            recipe = c.fetchall()[0]
            c.close()
            conn.close()
            gc.collect()
            if request.args.get('fav') == 'true':  # Insert recipe as a favourite in database
                c, conn = connection()
                _ = c.execute('SELECT favourites FROM users WHERE username = "%s"' % session['username'])
                favs = c.fetchall()[0][0]
                if favs is 'None':
                    _ = c.execute('UPDATE users SET favourites = "%s" WHERE username = "%s";' % (recipe[0], session['username']))
                    conn.commit()
                else:
                    favs = favs.split(',')
                    if str(recipe[0]) not in favs:
                        favs = ','.join(favs)+',%s' % recipe[0]
                        _ = c.execute('UPDATE users SET favourites = "%s" WHERE username = "%s";' % (favs, session['username']))
                        conn.commit()
                c.close()
                conn.close()
                gc.collect()
                return render_template('recipe.html', recipe=recipe, fav=True)

            elif request.args.get('fav') == 'false':  # Delete a favourite from the database
                c, conn = connection()
                _ = c.execute('SELECT favourites FROM users WHERE username = "%s"' % session['username'])
                favs = c.fetchall()[0][0]
                favs = favs.split(',')
                fav = str(recipe[0])
                if fav in favs:
                    idx = favs.index(fav)
                    _ = favs.pop(idx)
                    favs = ','.join(favs)
                    _ = c.execute('UPDATE users SET favourites = "%s" WHERE username = "%s";' % (favs, session['username']))
                    conn.commit()
                c.close()
                conn.close()
                gc.collect()
                return render_template('recipe.html', recipe=recipe, fav=False)
            return render_template('recipe.html', recipe=recipe)
        else:
            return redirect(url_for('list_recipes'))
    except Exception as e:
        return redirect(url_for('list_recipes'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
