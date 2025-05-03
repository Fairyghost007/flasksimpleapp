import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flasksite import app, db, bcrypt
from flasksite.forms import ProductForm, RegistrationForm, LoginForm, UpdateAccountForm
from flasksite.models import *
from flask_login import login_user, current_user, logout_user, login_required

    
@app.route("/")
@app.route("/home") 
def home():
    products = Product.query.all() 
    return render_template('home.html', 
                           products=products,
                           title='Home'
                          )
    
@app.route("/product/<int:product_id>")
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product, title=product.libelle)

from flask import flash

@app.route("/product/<int:product_id>/delete", methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.critical(f'Error while deleting product {product}')
        app.logger.exception(e)
        flash('There was an error deleting the product. Try again later.', 'danger')
    return redirect(url_for('home'))



@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            libelle=form.libelle.data,
            prix=form.prix.data,
            image_file=form.image_file.data.filename if form.image_file.data else None
        )
        db.session.add(product)
        db.session.commit()
        flash('Your product has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('product_form.html', form=form, legend='New Product')






@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        try:
            db.session.commit()
            app.logger.debug('New user created successfully.')
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.critical(f'Error while creating the user {user}')
            app.logger.exception(e)
            flash('The system encountered a problem while creating your account. Try again later.', 'danger')
    return render_template('register.html',
                           title='Register',
                           form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html',
                           title='Login',
                           form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_compressed_picture(form_picture):
    """
    Function that gets the file contained in the parameter `form_picture`, compresses it to a 125x125 pixels image,
    and saves it to the `static/profile_pics` folder.
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def save_raw_picture(form_picture):
    """
    Function that gets the file contained in the parameter `form_picture`,
    and saves it to the `static/profile_pics` folder.
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    form_picture.save(picture_path)

    return picture_fn