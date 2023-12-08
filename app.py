from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bcrypt import Bcrypt
from flask_ckeditor import CKEditor
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from webforms import LoginForm, PostForm, NamerForm, UserForm, PasswordForm, SearchForm
from sqlalchemy import desc
import uuid
import os

# Create a Flask Instance
app = Flask(__name__)
bcrypt = Bcrypt(app)
ckeditor = CKEditor(app)

# Add database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://yqkdqbwznberbc:5002011a1ba0926b830adc89202fb09c3ce1fa2b51789229c175fa6d243d2215@ec2-18-204-101-137.compute-1.amazonaws.com:5432/d6rhi33s7mi14l'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://:Passw0rd@localhost/our_users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Create a Migrate object
migrate = Migrate(app, db)

# Flask_Login stuff!
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Call the create_all method to create the tables
if __name__ == '__main__':
    with app.app_context():
        db.init_app(app)
        db.create_all()
    app.run()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Pass information to Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Create an admin page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 65:
        return render_template("admin.html")
    else:
        flash("You must be the administrator to access the admin page.")
        return redirect(url_for('dashboard'))

# Create search function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        searched_term = form.searched.data
        posts = posts.filter(Posts.content.like('%' + searched_term + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html", form=form, searched=searched_term, posts=posts)

# Create login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong password, try again!")
        else:
            flash("That user does not exist. Please create one.")

    return render_template('login.html', form=form)

# Create logout page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Create dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id 
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.favourite_color = request.form['favourite_color']
        name_to_update.about_author = request.form['about_author']
        name_to_update.profile_pic = request.files['profile_pic']
        # Grab image name
        pic_filename = secure_filename(name_to_update.profile_pic.filename)
        # Set UUID
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        # Save that image
        saver = request.files['profile_pic']
        # Change it to a string to save to db
        name_to_update.profile_pic = pic_name
        try:
            db.session.commit()
            saver.profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER']), pic_name)
            return redirect(url_for('dashboard'))
        except:
            flash("Error! There was a problem updating.")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)
    return render_template('dashboard.html')

@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            posts = Posts.query.order_by(desc(Posts.date_posted))
            return render_template("posts.html", posts=posts)
        except:
            flash("There was a problem deleting the post. Try again!")
            posts = Posts.query.order_by(desc(Posts.date_posted))
            return render_template("posts.html", posts=posts)
    else:
        flash("You must be logged in as the correct user to delete this post!")
        posts = Posts.query.order_by(desc(Posts.date_posted))
        return render_template("posts.html", posts=posts)

@app.route('/posts')
def posts():

    #Grab all the posts from the database
    posts = Posts.query.order_by(desc(Posts.date_posted))
    return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
@login_required
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form  = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data 
        post.content = form.content.data 
        # Add to database
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('post', id=post.id))

    if current_user.id == post.poster.id:
        form.title.data = post.title
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You are not authorised to edit this post!")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

# Add post page
@app.route('/add-post', methods=['GET', 'POST'])
# @login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
        # Clear the form
        form.title.data = ''
        form.content.data = ''
        # form.author.data = ''
        form.slug.data = ''

        # Add post to the database
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('posts'))

    # Redirect to another web page
    return render_template("add_post.html", form=form)

# JSON thing
@app.route('/date')
def get_current_date():
    favourite_pizza = {"John": "Pepporoni", "Mary": "Cheese", "Tim": "Mushroom"}
    return favourite_pizza
    # return {"Date": date.today()}

# Create secret key
app.config['SECRET_KEY'] = "My secret key"

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        our_users = Users.query.order_by(Users.date_added)
        return redirect(url_for('add_user')) 
    except:
        flash("There was a problem deleting user.")
        return render_template("add_user.html", form=form, name=name, our_users=our_users) 

# Update database record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.favourite_color = request.form['favourite_color']
        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except:
            flash("Error! There was a problem updating.")
            return render_template("update.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the password!!!
            hashed_pw = bcrypt.generate_password_hash(form.password_hash.data).decode('utf-8')
            user = Users(username=form.username.data, name=form.name.data, email=form.email.data, favourite_color=form.favourite_color.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
            name = form.name.data
            form.name.data = ''
            form.username.data = ''
            form.email.data = ''
            form.favourite_color = ''
            form.password_hash.data = ''
        else:
            flash("User already exists!", "danger")

    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form=form, name=name, our_users=our_users)

# Create a route decorator
@app.route('/')
def index():
    first_name = "Dan"
    stuff = "This is <strong>bold</strong> text"
    favourite_pizza = ["Pepporoni", "Cheese", "Mushroom", 41]
    return render_template("index.html", first_name=first_name, stuff=stuff, favourite_pizza=favourite_pizza)

@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)

# Create custom error pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

# Create Test Password Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''

        # Look up user by email
        pw_to_check = Users.query.filter_by(email=email).first()

        # Check hashed password
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template("test_pw.html", email=email, passed=passed, password=password, pw_to_check=pw_to_check, form=form)

# Create Name Page
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NamerForm()

    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''

    return render_template("name.html", name=name, form=form)

if __name__ == '__main__':
    app.run()

# Create a blog post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# Create a model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favourite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(), nullable=True)

     # Do some password stuff
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        # Use Flask-Bcrypt to generate the password hash
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name

if __name__ == '__main__':
    app.run()





# Deploy Flask App With Database On Heroku For Webhosting - Flask Fridays #39
# git push

# cd /c/flasker/
# source virtual/Scripts/activate
# export FLASK_DEBUG=1
# export FLASK_APP=hello.py
# flask run
# http://127.0.0.1:5000
# https://flasker619-a17cb4d0deca.herokuapp.com/
# postgres://yqkdqbwznberbc:5002011a1ba0926b830adc89202fb09c3ce1fa2b51789229c175fa6d243d2215@ec2-18-204-101-137.compute-1.amazonaws.com:5432/d6rhi33s7mi14l