# routes.py
from flask import Blueprint, render_template,  redirect, url_for, request, flash, current_app
from flask_login import current_user, login_required
from models import User
from sqlalchemy import func
from datetime import datetime, timedelta
from models import EnergyUsage, Recommendations
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use this backend before importing pyplot
import matplotlib.pyplot as plt
from __init__ import db

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def index():
    return render_template('index.html')

# User-specific routes
@routes_bp.route('/users/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))
    
    # Get the most recent recommendation
    most_recent_recommendation = Recommendations.query.filter_by(user_id=current_user.id).order_by(Recommendations.id.desc()).first()
    
    # Calculate average units used for water and electricity
    average_electricity = db.session.query(func.round(func.avg(EnergyUsage.units_used))).filter(
        EnergyUsage.user_id == current_user.id, 
        EnergyUsage.energy_type == 'electricity'
    ).scalar() or 0  # Default to 0 if no records are found

    average_water = db.session.query(func.round(func.avg(EnergyUsage.units_used))).filter(
        EnergyUsage.user_id == current_user.id, 
        EnergyUsage.energy_type == 'water'
    ).scalar() or 0  # Default to 0 if no records are found
    return render_template('Users/user_dashboard.html', most_recent_recommendation=most_recent_recommendation, average_electricity=average_electricity, average_water=average_water)

@routes_bp.route('/users/data_entry', methods=['GET', 'POST'])
@login_required
def data_entry():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    if request.method == 'POST':
        # Get data from form
        energy_type = request.form.get('energyType')
        units_used = request.form.get('unitsUsed')
        date_recorded = request.form.get('date')

        new_usage = EnergyUsage(
            user_id=current_user.id,
            energy_type=energy_type,
            units_used=units_used,
            date_recorded=datetime.strptime(date_recorded, '%Y-%m-%d')
        )

        # Add to the session and commit
        db.session.add(new_usage)
        try:
            db.session.commit()
            flash('Energy usage recorded successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Unable to record energy usage.', 'error')

        # Redirect to a new page or the same page to show a success message or to clear the form
        return redirect(url_for('routes.data_entry'))

    # GET request - just render the template
    return render_template('Users/data_entry.html')

from flask import request
from sqlalchemy import func
from datetime import datetime, timedelta

@routes_bp.route('/users/history')
@login_required
def history():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    # Get the selected time period, aggregation, and energy type from the dropdown menus
    time_period = request.args.get('time_period', '7 days')  # Default to last 7 days
    energy_type = request.args.get('energy_type', 'electricity')  # Default to electricity
    
    # Adjust the query based on the selected time period and energy type
    if time_period == '7 days':
        start_date = datetime.now() - timedelta(days=7)
    elif time_period == '30 days':
        start_date = datetime.now() - timedelta(days=30)
    elif time_period == '3 months':
        start_date = datetime.now() - timedelta(days=90)  # Assuming 3 months = 90 days
    elif time_period == '6 months':
        start_date = datetime.now() - timedelta(days=180)  # Assuming 6 months = 180 days
    
    # Filter the records based on time period and energy type
    records = EnergyUsage.query.filter(EnergyUsage.user_id == current_user.id,
                                       EnergyUsage.energy_type == energy_type,
                                       EnergyUsage.date_recorded >= start_date).all()
    
    # Get the value of the aggregation parameter
    aggregation = request.args.get('aggregate', 'all')  # Default to all records
    
    if aggregation == 'aggregate':
        # Calculate the total units used and average units used
        total_units_used = sum(record.units_used for record in records)
        average_units_used = total_units_used / len(records) if records else 0
        records = None  # Reset records to None since we're showing aggregates
        show_aggregate = True
    else:
        total_units_used = None
        average_units_used = None
        show_aggregate = False
    
    return render_template('Users/history.html', records=records, time_period=time_period,
                           total_units_used=total_units_used, average_units_used=average_units_used,
                           aggregation=aggregation, show_aggregate=show_aggregate)

import os

@routes_bp.route('/users/power_usage')
@login_required
def power_usage():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    energy_types = ['electricity', 'water', 'naturalgas', 'vehiclefuel']
    latest_graphs = {}

    for energy_type in energy_types:
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=10)
        energy_data = EnergyUsage.query.filter(
            EnergyUsage.user_id == current_user.id,
            EnergyUsage.energy_type == energy_type,
            EnergyUsage.date_recorded >= start_date,
            EnergyUsage.date_recorded <= end_date
        ).all()

        if not energy_data:
            latest_graphs[energy_type] = {'bar_graph_exists': False, 'line_graph_exists': False}
            continue

        weekly_dates = [(end_date - timedelta(weeks=i)).strftime('%Y-%m-%d') for i in range(10)]
        weekly_usage = [sum(data.units_used for data in energy_data if data.date_recorded.strftime('%Y-%m-%d') == date) for date in weekly_dates]
        all_time_dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(21)]
        all_time_usage = [sum(data.units_used for data in energy_data if data.date_recorded.strftime('%Y-%m-%d') == date) for date in all_time_dates]

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        bar_graph_filename = f'{energy_type}_bar_graph_{timestamp}.png'
        line_graph_filename = f'{energy_type}_line_graph_{timestamp}.png'

        # Save bar graph
        bar_graph_path = os.path.join(current_app.root_path, 'static', 'Images', bar_graph_filename)
        plt.figure(figsize=(10, 6))
        plt.bar(weekly_dates, weekly_usage)
        plt.xlabel('Date')
        plt.ylabel('Energy Usage')
        plt.title(f'Weekly {energy_type.capitalize()} Usage')
        plt.xticks(rotation=45)
        plt.savefig(bar_graph_path, format='png')
        plt.close()

        # Save line graph
        line_graph_path = os.path.join(current_app.root_path, 'static', 'Images', line_graph_filename)
        plt.figure(figsize=(10, 6))
        plt.plot(all_time_dates, all_time_usage, marker='o')
        plt.xlabel('Date')
        plt.ylabel('Energy Usage')
        plt.title(f'All-Time {energy_type.capitalize()} Usage')
        plt.xticks(rotation=45)
        plt.savefig(line_graph_path, format='png')
        plt.close()

        # Store the latest file names
        latest_graphs[energy_type] = {
            'bar_graph_exists': True, 'bar_graph_filename': bar_graph_filename,
            'line_graph_exists': True, 'line_graph_filename': line_graph_filename
        }

    return render_template('Users/power_usage.html', latest_graphs=latest_graphs)

@routes_bp.route('/users/recommendations')
@login_required
def recommendations():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))
    
    # Define energy types
    energy_types = ['electricity', 'water', 'naturalgas', 'vehiclefuel']
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    latest_recommendations = []

    for energy_type in energy_types:
        energy_data = EnergyUsage.query.filter(
            EnergyUsage.user_id == current_user.id,
            EnergyUsage.energy_type == energy_type,
            EnergyUsage.date_recorded >= start_date,
            EnergyUsage.date_recorded <= end_date
        ).order_by(EnergyUsage.date_recorded.desc()).all()

        if not energy_data:
            continue

        # Find the latest date for current energy type data
        latest_date = max(data.date_recorded for data in energy_data)

        usage_values = [data.units_used for data in energy_data if data.date_recorded == latest_date]
        first_quartile = np.percentile(usage_values, 25)
        third_quartile = np.percentile(usage_values, 75)
        max_usage = max(usage_values)

        for data in energy_data:
            if data.date_recorded == latest_date:
                if data.units_used < first_quartile:
                    recommendation = "Congratulations! Your energy usage is below average."
                elif data.units_used > third_quartile:
                    recommendation = "Consider reducing energy usage. Your usage is higher than usual."
                elif data.units_used == max_usage:
                    recommendation = "Warning! Your energy usage today is the highest recorded in the past week."
                else:
                    recommendation = "No specific recommendation for today. Continue to monitor energy usage."

                db_recommendation = Recommendations(user_id=current_user.id, recommendation=recommendation, date_recorded=data.date_recorded, energy_type=energy_type)
                db.session.add(db_recommendation)
                
                latest_recommendations.append((data.date_recorded, energy_type, recommendation))

    db.session.commit()
    return render_template('Users/recommendations.html', all_recommendations=latest_recommendations)
@routes_bp.route('/users/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    if request.method == 'POST':
        # Get the form data
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        current_password = request.form.get('currentPassword')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')

        # Check if current password matches the user's password
        if not current_user.check_password(current_password):
            flash('Incorrect current password. Please try again.', 'error')
            return redirect(url_for('routes.settings'))

        # Update user details if provided
        if firstname:
            current_user.firstname = firstname
        if lastname:
            current_user.lastname = lastname
        if email:
            current_user.email = email

        # Change password if new password is provided and matches the confirm password
        if new_password and new_password == confirm_password:
            current_user.set_password(new_password)

        # Commit changes to the database
        db.session.commit()

        flash('Your settings have been updated successfully.', 'success')

    return render_template('Users/settings.html')

# Admin-specific routes
@routes_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('routes.user_dashboard'))

    # Calculate average units used for electricity and water
    average_electricity = db.session.query(func.round(func.avg(EnergyUsage.units_used))).filter_by(energy_type='electricity').scalar() or 0
    average_water = db.session.query(func.round(func.avg(EnergyUsage.units_used))).filter_by(energy_type='water').scalar() or 0

    return render_template('Admin/admin_dashboard.html',
                           average_electricity=average_electricity,
                           average_water=average_water)

@routes_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for('routes.user_dashboard'))

    all_users = User.query.all()
    return render_template('Admin/users.html', all_users=all_users)


@routes_bp.route('/Admin/history/<int:user_id>')
@login_required
def history_user(user_id):
    # Check if the current user is an admin
    if not current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    # Fetch the user whose history is to be viewed
    user = User.query.get(user_id)
    if user is None:
        return "User not found", 404

    # Extract query parameters
    time_period = request.args.get('time_period', '7 days')  # Default to last 7 days
    energy_type = request.args.get('energy_type', 'electricity')  # Default to electricity
    aggregation = request.args.get('aggregate', 'all')  # Default to all records

    # Compute start date based on the time period
    if time_period == '7 days':
        start_date = datetime.now() - timedelta(days=7)
    elif time_period == '30 days':
        start_date = datetime.now() - timedelta(days=30)
    elif time_period == '3 months':
        start_date = datetime.now() - timedelta(days=90)
    elif time_period == '6 months':
        start_date = datetime.now() - timedelta(days=180)

    # Query the energy usage records
    records = EnergyUsage.query.filter(EnergyUsage.user_id == user.id,
                                       EnergyUsage.energy_type == energy_type,
                                       EnergyUsage.date_recorded >= start_date).all()

    # Compute aggregates if needed
    if aggregation == 'aggregate':
        total_units_used = sum(record.units_used for record in records)
        average_units_used = total_units_used / len(records) if records else 0
        records = None  # Optional: Clear records if only showing aggregates
    else:
        total_units_used = None
        average_units_used = None

    # Render the template with the user's data
    return render_template('Admin/history.html', records=records, time_period=time_period,
                           total_units_used=total_units_used, average_units_used=average_units_used,
                           aggregation=aggregation, user=user)