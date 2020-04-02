import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout

# Why not use session instead of g? Is to to avoid self-referencing?
# easier to store object/instance into g rather than session (session  only  for primitives)
# g is cleared after every request - thats why we add-user-to-g before each request

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

# confirm naming convention here with "do"


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash(f"Successfully logged out {g.user.username}", 'info')
    return redirect("/login")


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    likes = Likes.query.filter_by(user_id=user_id).all()
    likes_list = [l.message_id for l in likes]

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages, likes=likes_list)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = EditUserForm(obj=g.user)

    if form.validate_on_submit():
        password = form.password.data
        user_valid = User.authenticate(g.user.username, password)

        if not user_valid:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        username = form.username.data
        email = form.email.data
        image_url = form.image_url.data or None
        header_image_url = form.header_image_url.data or None
        bio = form.bio.data
        location = form.location.data

        g.user.username = username
        g.user.email = email

        # Keep current URL if they left it blank
        if image_url:
            g.user.image_url = image_url
            
        # Keep current URL if they left it blank
        if header_image_url:
            g.user.header_image_url = header_image_url
        g.user.bio = bio
        g.user.location = location

        db.session.commit()

        return redirect(f'/users/{g.user.id}')

    else:
        return render_template('/users/edit.html',
                               form=form,
                               user_id=g.user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    likes = Likes.query.filter_by(user_id=user_id).all()

    ## Use a set b/c it only has keys and O(1) searching because you're searching for that specific key
    ## set comprehension syntax - replace with curly braces
    ## jinja syntax will be the same

    ## watch out for these variable names
    like_ids = [l.message_id for l in likes]

    messages = (Message
                .query
                .filter(Message.user_id == g.user.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg, messages=messages, likes=like_ids)

    ## when we pass it to the template, call it like_ids instead


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Likes routes:

@app.route('/messages/<int:message_id>/like', methods=["POST"])
def like_message(message_id):
    """allows user to like a message and save it to a liked message page"""
    current_msg_like = Likes(user_id=g.user.id, message_id=message_id)
    db.session.add(current_msg_like)
    db.session.commit()
    return redirect('/')


@app.route('/users/<int:user_id>/likes')
def likes_page(user_id):
    """takes user to page of likes"""

    likes = Likes.query.filter_by(user_id=user_id).all()
    likes_list = [l.message_id for l in likes]

    messages = Message.query.filter(Message.id.in_(likes_list))

    # print("\n\n\n this is likes list\n\n\n", likes_list)

    return render_template('messages/likes.html',
                           user=g.user,
                           messages=messages,
                           likes=likes_list)


@app.route('/messages/<int:message_id>/unlike', methods=["POST"])
def unlike_message(message_id):
    """Unlikes a message and removes it from our likes 
    database and redirects to the user likes page"""

    current_msg = Likes.query.filter_by(message_id=message_id).first()
    print("\n\n\n this is current msg  \n\n\n", current_msg)
    db.session.delete(current_msg)
    db.session.commit()

    return redirect(f'/users/{g.user.id}/likes')


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    users_list = [u.id for u in g.user.following]
    print("\n\n\n this is our users_list\n\n\n", users_list)
    if g.user:
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(users_list))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        likes = Likes.query.filter_by(user_id=g.user.id).all()
        likes_list = [l.message_id for l in likes]

        return render_template('home.html',
                               messages=messages, 
                               likes=likes_list)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
