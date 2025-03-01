from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from flask_mail import Mail, Message # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash
import os
from itsdangerous import URLSafeTimedSerializer
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

# MongoDB configuration
app.config['MONGO_URI'] = 'mongodb://localhost:27017/contact_db'
mongo = PyMongo(app)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shadiomondi22@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'zosv kfcd prns ccoy'     # Replace with your app password
mail = Mail(app)

# Token serializer for password reset
serializer = URLSafeTimedSerializer(app.secret_key)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hashpass = generate_password_hash(request.form['password'])
            users.insert_one({
                'username': request.form['username'],
                'password': hashpass,
                'email': request.form['email']
            })
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        flash('Username already exists!', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})

        if login_user:
            if check_password_hash(login_user['password'], request.form['password']):
                session['username'] = request.form['username']
                return redirect(url_for('dashboard'))
        
        flash('Invalid username/password combination', 'error')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = mongo.db.users.find_one({'email': email})
        
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            msg = Message('Password Reset Request',
                         sender='your-email@gmail.com',
                         recipients=[email])
            msg.body = f'To reset your password, visit the following link: {reset_url}'
            mail.send(msg)
            
            flash('Password reset instructions sent to your email.', 'success')
            return redirect(url_for('login'))
            
        flash('Email address not found.', 'error')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashpass = generate_password_hash(new_password)
        
        mongo.db.users.update_one(
            {'email': email},
            {'$set': {'password': hashpass}}
        )
        
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/add-contact', methods=['GET', 'POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        contacts = mongo.db.contacts
        contacts.insert_one({
            'mobile': request.form['mobile'],
            'email': request.form['email'],
            'address': request.form['address'],
            'registration_number': request.form['registration_number'],
            'username': session['username']
        })
        flash('Contact added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_contact.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        reg_number = request.form['registration_number']
        contact = mongo.db.contacts.find_one({'registration_number': reg_number})
        return render_template('search.html', contact=contact)
    return render_template('search.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)