# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from __init__ import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to the dashboard based on whether the user is an admin or not
        return redirect(url_for('routes.admin_dashboard')) if current_user.is_admin else redirect(url_for('routes.user_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            # Redirect to the dashboard based on whether the user is an admin or not
            return redirect(url_for('routes.admin_dashboard')) if user.is_admin else redirect(url_for('routes.user_dashboard'))
        flash('Invalid username or password')
    return render_template('Auth/user_login.html')  # Use a generic login template or separate ones if preferred


@auth_bp.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if current_user.is_authenticated:
        return redirect(url_for('routes.user_dashboard'))
    if request.method == 'POST':
        # Extract form data
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password1')
        electricity_meter_number = request.form.get('electricity_meter_number')
        water_meter_number = request.form.get('water_meter_number')

        # Validate password match and email uniqueness
        if password != password_confirm:
            flash('Passwords must match.')
            return redirect(url_for('auth.user_signup'))
        
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already in use.')
            return redirect(url_for('auth.user_signup'))

        # Create new user instance
        new_user = User(
            firstname=first_name, 
            lastname=last_name, 
            email=email, 
            electricity_meter_number=electricity_meter_number,
            water_meter_number=water_meter_number,
            is_admin=False
        )
        new_user.set_password(password)

        # Add new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!')
        return redirect(url_for('auth.login'))
    
    return render_template('Auth/user_signup.html')

@auth_bp.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if current_user.is_authenticated:
        return redirect(url_for('routes.user_dashboard'))
    if request.method == 'POST':
        # Extract form data
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password1')

        # Validate password match and email uniqueness
        if password != password_confirm:
            flash('Passwords must match.')
            return redirect(url_for('auth.user_signup'))
        
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already in use.')
            return redirect(url_for('auth.user_signup'))

        # Create new user instance
        new_user = User(
            firstname=first_name, 
            lastname=last_name, 
            email=email, 
            is_admin=True
        )
        new_user.set_password(password)

        # Add new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!')
        return redirect(url_for('auth.login'))
    
    return render_template('Auth/admin_signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))  # Adjust to your landing page route
