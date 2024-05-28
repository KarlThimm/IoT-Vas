# auth.py

import psycopg

from psycopg.rows import class_row
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User


auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    name = request.form.get('name')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    with psycopg.connect("host=db user=postgres password=admin") as conn:
        with conn.cursor(row_factory=class_row(User)) as cur:
            user = cur.execute("SELECT * FROM users WHERE name = %s LIMIT 1", (name,)).fetchone()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if user is None or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    name = request.form.get('name')
    password = request.form.get('password')
    password_hash = generate_password_hash(password)
    remember = True if request.form.get('remember') else False

    with psycopg.connect("host=db user=postgres password=admin") as conn:
        with conn.cursor(row_factory=class_row(User)) as cur:
            user = cur.execute("SELECT * FROM users WHERE name = %s LIMIT 1", (name,)).fetchone()

            if user is not None: # if a user is found, we want to redirect back to signup page so user can try again  
                flash('Name already exists')
                return redirect(url_for('auth.signup'))

            # add the new user to the database
            cur.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (name, password_hash))

    login_user(User(name, password_hash), remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
