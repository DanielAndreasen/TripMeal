from flask import Flask, render_template, flash, jsonify, request, url_for, \
                  redirect, session, g
from dbconnect import connection
from MySQLdb import escape_string
from wtforms import Form, TextField, PasswordField, BooleanField, validators, TextAreaField, StringField, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import random
import gc
import os


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email address', [validators.Length(min=5, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm',
                                                             message='Passwords must match')])
    confirm = PasswordField('Repeat password')


class RecipeForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    country = SelectField('Country')
    ingredients = TextAreaField('Ingredients', [validators.Length(min=5)])
    recipe = TextAreaField('Recipe', [validators.Length(min=30)])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            username = session['username']
        except KeyError:
            username = None
        if username is None:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def get_recipes(rid):
    """rid can be an integer or 'all'.
    Return a dictionary with the rid and title"""
    c, conn = connection()
    if rid == 'all':
        _ = c.execute('SELECT rid, title FROM recipes;')
        d = c.fetchall()
        rid_dict = {int(di[0]): di[1] for di in d}
        c.close()
        conn.close()
        gc.collect()
        return rid_dict
    else:
        _ = c.execute('SELECT rid, title FROM recipes WHERE rid = ("%s");' % rid)
        d = c.fetchall()[0]
        rid_dict = {int(d[0]): d[1]}
        c.close()
        conn.close()
        gc.collect()
        return rid_dict


def get_ranking():
    c, conn = connection()
    _ = c.execute('SELECT user, COUNT(*) AS nu FROM recipes GROUP BY user ORDER BY nu DESC;')
    d = c.fetchall()
    c.close()
    conn.close()
    gc.collect()

    d = {name: int(count) for name, count in d}
    return d


def convert2HTML(text):
    if ('1.' in text) and ('2.' in text) and ('3.' in text):  # We have a list here
        final = 1
        for line in text.split('\r\n'):
            if line.startswith('%s.' % final):
                final += 1

        newtext = ''
        i = 1
        for line in text.split('\r\n'):
            if line.startswith('%s.' % i):
                if i == 1:
                    newtext += '<ol>\r\n'
                i += 1
                newline = '<li>' + line[2:] + '</li>\r\n'
                newtext += newline
                if i == final:
                    newtext +=  '</ol>'
            else:
                newtext += line + '\r\n'
        return newtext

    else:
        return text


# Setup Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['TRIPMEAL_KEY']


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route('/login/', methods=['GET', 'POST'])
def login_page():
    try:
        error = None
        c, conn = connection()
        if request.method == 'POST':
            username = escape_string(request.form['username']).decode()
            data = c.execute('SELECT * FROM users WHERE username = ("%s");' % username)
            data = c.fetchone()
            if sha256_crypt.verify(request.form['password'], data[2]) and (data[1] == username):
                session['logged_in'] = True
                session['username'] = username
                session['favourites'] = data[4]
                flash('You are now logged in')
                return redirect(url_for('user_page'))
            else:
                error = 'Invalid credentials, try again'
        gc.collect()
        return render_template('login.html', error=error)
    except:
        error = 'Invalid credentials, try again'
        return render_template('login.html', error=error)


@app.route('/logout/')
@login_required
def logout_page():
    if session['logged_in']:
        session['logged_in'] = False
        session['username'] = None
    return redirect(url_for('list_recipes'))


@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm(request.form)
    try:
        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))

            c, conn = connection()
            x = c.execute('SELECT * FROM users WHERE username = ("%s");' %
                             escape_string(username))
            if int(x) > 0:
                flash('That username is already taken, please choose another')
                return render_template('register.html', form=form)
            else:
                c.execute('INSERT INTO users (username, password, email) VALUES ("%s", "%s", "%s");' %
                          (escape_string(username), escape_string(password), escape_string(email)))
                conn.commit()
                flash('Thanks for registering!')
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('favourites_page'))
        return render_template('register.html', form=form)
    except Exception as e:
        return render_template('register.html', form=form)


@app.route('/newrecipe/', methods=['GET', 'POST'])
@login_required
def newrecipe():
    if request.method == 'POST':
        pass
        # print request.form
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


@app.route('/recipe', methods=['POST', 'GET'], strict_slashes=False)
def list_recipe():
    try:
        if request.method == 'GET':
            rid = request.args.get('rid')
            c, conn = connection()
            _ = c.execute('SELECT * FROM recipes WHERE rid = %s;' % escape_string(rid))
            recipe = list(c.fetchall()[0])
            recipe[4] = convert2HTML(recipe[4])
            c.close()
            conn.close()
            gc.collect()
            if request.args.get('fav') == 'true':  # Insert recipe as a favourite in database
                c, conn = connection()
                _ = c.execute('SELECT favourites FROM users WHERE username = "%s";' % session['username'])
                favs = c.fetchall()[0][0]
                if favs is None:
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
                _ = c.execute('SELECT favourites FROM users WHERE username = "%s";' % session['username'])
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
            else:
                try:
                    logged_in = session['logged_in']
                except KeyError:
                    logged_in = False
                if logged_in:
                    c, conn = connection()
                    _ = c.execute('SELECT favourites FROM users WHERE username = ("%s");' % session['username'])
                    try:
                        favs = c.fetchall()[0][0].split(',')
                    except Exception:  # No favs yet
                        return render_template('recipe.html', recipe=recipe, fav=False)
                    c.close()
                    conn.close()
                    gc.collect()
                    return render_template('recipe.html', recipe=recipe, fav=rid in favs)
                else:
                    return render_template('recipe.html', recipe=recipe, fav=False)
        else:
            return redirect(url_for('list_recipes'))
    except Exception as e:
        return redirect(url_for('list_recipes'))


@app.route('/favourites/')
@login_required
def favourites_page():
    try:
        c, conn = connection()
        _ = c.execute('SELECT favourites FROM users WHERE username = ("%s");' % session['username'])
        favs = c.fetchall()[0][0]
        c.close()
        conn.close()
        gc.collect()
        try:
            favs = filter(None, favs.split(','))
        except Exception:
            return render_template('favourites.html', favourites=False)
        fav_dict = {}
        for fav in favs:
            c, conn = connection()
            _ = c.execute('SELECT title FROM recipes WHERE rid = ("%s");' % fav)
            fav_dict[fav] = c.fetchall()[0][0]
            c.close()
            conn.close()
            gc.collect()
        return render_template('favourites.html', favourites=fav_dict)
    except Exception as e:
        return render_template('favourites.html', favourites=False)


@app.route('/menu/')
def menu_page():
    try:
        logged_in = session['logged_in']
    except KeyError:
        logged_in = False
    menu_dict = {}
    n_favourites = 0
    all_recipes = get_recipes('all')
    rids = all_recipes.keys()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if logged_in:  # Include favourites
        try:
            c, conn = connection()
            _ = c.execute('SELECT favourites FROM users WHERE username = ("%s");' % session['username'])
            d = c.fetchall()[0][0]
            favs = map(int, filter(None, d.split(',')))
            c.close()
            conn.close()
            gc.collect
            n_favourites = len(favs)
        except Exception:
            pass
        if n_favourites:
            while len(favs):
                rid = random.choice(favs)
                favs.pop(favs.index(rid))  # Don't use the same recipe twice per week
                tmp = {rid: all_recipes[rid]}
                day = random.choice(days)
                days.pop(days.index(day))
                menu_dict[day] = [rid, tmp[rid]]

    for _ in range(7-n_favourites):
        day = random.choice(days)
        days.pop(days.index(day))
        rid = random.choice(rids)
        tmp = {rid: all_recipes[rid]}
        menu_dict[day] = [rid, tmp[rid]]

    return render_template('menu.html', menu=menu_dict)


@app.route('/user/')
@login_required
def user_page():
    try:
        user = session['username']
        c, conn = connection()
        if user == 'Daniel':
            _ = c.execute('SELECT rid, location, title FROM recipes;')
        else:
            _ = c.execute('SELECT rid, location, title FROM recipes WHERE user="%s";' % user)
        recipes = c.fetchall()
        c.close()
        conn.close()
        gc.collect()

        recipes = [
            {
                'rid': recipe[0],
                'country': recipe[1],
                'title': recipe[2]
             } for recipe in recipes]

        rank = get_ranking()
        if user not in rank.keys():
            number_recipes = 0
        else:
            number_recipes = rank[user]
        total_recipes = sum(rank.values())
        return render_template('user.html', user=user, nr=number_recipes, tr=total_recipes, recipes=recipes)
    except Exception as e:
        return render_template('favourites.html', favourites=False)


@app.route('/edit_recipe/<string:rid>', methods=['GET', 'POST'])
@login_required
def edit_recipe(rid):
    # Get the recipe
    # c.execute('INSERT INTO recipes (title, location, ingredients, recipe, user) VALUES ("%s", "%s", "%s", "%s", "%s");' %
    c, conn = connection()
    _ = c.execute('SELECT * FROM recipes WHERE rid="%s"' % rid)
    recipe = c.fetchone()
    c.close()
    conn.close()
    gc.collect()

    # Fill the form
    form = RecipeForm(request.form)
    form.title.data = recipe[1]
    form.country.data = recipe[2]
    form.ingredients.data = '\n'.join(recipe[3].split(','))
    form.recipe.data = recipe[4]

    if request.method == 'POST':
        title = escape_string(request.form['title'])
        country = escape_string(request.form['country'])
        ingredients = escape_string(','.join(request.form['ingredients'].split('\r\n')).strip(','))
        recipe = escape_string(request.form['recipe'])

        # Update the DB
        c, conn = connection()
        c.execute('UPDATE recipes SET title="%s", location="%s", ingredients="%s", recipe="%s" WHERE rid=%s' % (title, country, ingredients, recipe, rid))
        conn.commit()

        # Close connection
        c.close()
        conn.close()
        gc.collect()

        flash('Recipe updated')

        return redirect(url_for('user_page'))

    return render_template('edit_recipe.html', form=form)


@app.route('/delete_recipe/<string:rid>', methods=['GET', 'POST'])
@login_required
def delete_recipe(rid):
    username = session['username']
    if request.method == 'POST':
        c, conn = connection()
        if username == 'Daniel':
            _ = c.execute('DELETE FROM recipes WHERE rid="%s"' % (rid))
        else:
            _ = c.execute('DELETE FROM recipes WHERE rid="%s" AND user="%s"' % (rid, username))
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        flash('Recipe successfully deleted')
        return redirect(url_for('user_page'))
    else:
        flash('Recipe not deleted')
        return redirect(url_for('user_page'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
