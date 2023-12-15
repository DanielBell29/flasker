from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime, date
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# Create a Flask Instance
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Passw0rd@localhost/our_users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Create a Migrate object
migrate = Migrate(app, db)

# Flask_Login stuff!
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

# Create login form
class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")

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
				flash("You are now logged in!")
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
	flash("You have been logged out!")
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
		try:
			db.session.commit()
			flash("User Updated Successfully!")
			return redirect(url_for('dashboard'))
		except:
			flash("Error! There was a problem updating.")
			return render_template("dashboard.html", form=form, name_to_update=name_to_update)
	else:
		return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)
	return render_template('dashboard.html')

# Create a blog post model
class Posts(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	content = db.Column(db.Text)
	author = db.Column(db.String(255))
	date_posted = db.Column(db.DateTime, default=datetime.utcnow)
	slug = db.Column(db.String(255))

# Create a posts form
class PostForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired()])
	content = StringField("Content", validators=[DataRequired()], widget=TextArea())
	author = StringField("Author", validators=[DataRequired()])
	slug = StringField("Slug", validators=[DataRequired()])
	submit = SubmitField("Submit")

@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
def delete_post(id):
	post_to_delete = Posts.query.get_or_404(id)

	try:
		db.session.delete(post_to_delete)
		db.session.commit()
		flash("Post has been deleted!")
		posts = Posts.query.order_by(desc(Posts.date_posted))
		return render_template("posts.html", posts=posts)
	except:
		flash("There was a problem deleting the post. Try again!")
		posts = Posts.query.order_by(desc(Posts.date_posted))
		return render_template("posts.html", posts=posts)

@app.route('/posts')
def posts():

	#Grab all the posts from the database
	posts = Posts.query.order_by(desc(Posts.date_posted))
	return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
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
		post.author = form.author.data 
		post.slug = form.slug.data 
		post.content = form.content.data 
		# Add to database
		db.session.add(post)
		db.session.commit()
		flash("Post has been updated!")
		return redirect(url_for('post', id=post.id))
	form.title.data = post.title
	form.author.data = post.author
	form.slug.data = post.slug
	form.content.data = post.content
	return render_template('edit_post.html', form=form)

# Add post page
@app.route('/add-post', methods=['GET', 'POST'])
# @login_required
def add_post():
	form = PostForm()
	if form.validate_on_submit():
		post = Posts(title=form.title.data, content=form.content.data, author=form.author.data, slug=form.slug.data)
		# Clear the form
		form.title.data = ''
		form.content.data = ''
		form.author.data = ''
		form.slug.data = ''

		# Add post to the database
		db.session.add(post)
		db.session.commit()
		flash("Blog post submitted successfully!")

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

# Create a model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favourite_color = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Do some password stuff
    password_hash = db.Column(db.String(500))
    @property 
    def password(self):
    	raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
    	self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
    	return check_password_hash(self.password_hash, password)

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name

@app.route('/delete/<int:id>')
def delete(id):
	user_to_delete = Users.query.get_or_404(id)
	name = None
	form = UserForm()
	try:
		db.session.delete(user_to_delete)
		db.session.commit()
		flash("User deleted successfully!")
		our_users = Users.query.order_by(Users.date_added)
		return redirect(url_for('add_user')) 
	except:
		flash("There was a problem deleting user.")
		return render_template("add_user.html", form=form, name=name, our_users=our_users) 

class PasswordForm(FlaskForm):
	email = StringField("What's your Email?", validators=[DataRequired()])
	password_hash = PasswordField("What's your Password?", validators=[DataRequired()])
	submit = SubmitField("Submit")

# Create a Form Class
class NamerForm(FlaskForm):
	name = StringField("What's your name?", validators=[DataRequired()])
	submit = SubmitField("Submit")

# Update database record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
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
			flash("User Updated Successfully!")
			return redirect(url_for('dashboard'))
		except:
			flash("Error! There was a problem updating.")
			return render_template("update.html", form=form, name_to_update=name_to_update)
	else:
		return render_template("update.html", form=form, name_to_update=name_to_update, id=id)


# Create a Form Class
class UserForm(FlaskForm):
	name = StringField("Name", validators=[DataRequired()])
	username = StringField("Username", validators=[DataRequired()])
	email = StringField("Email", validators=[DataRequired()])
	favourite_color = StringField("Favourite Color")
	password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords must match!')])
	password_hash2 = PasswordField('Confirm password', validators=[DataRequired()])
	submit = SubmitField("Submit")

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
			flash("User added successfully!", "success")
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
		form.name.date = ''
		flash("Form submitted successfully!")

	return render_template("name.html", name=name, form=form)

#if __name__ == '__main__':
#    with app.app_context():
#        db.create_all()
#    app.run()

if __name__ == '__main__':
    app.run()


# Clean Up Our Flask Code! - Flask Fridays #26
# git push

# cd /c/flasker/
# source virtual/Scripts/activate
# export FLASK_DEBUG=1
# export FLASK_APP=hello.py
# flask run