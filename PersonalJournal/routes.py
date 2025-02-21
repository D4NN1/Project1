from datetime import datetime, timedelta
import calendar
import os
import secrets
from PersonalJournal import db, login_manager, app
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, flash, redirect, abort
from PersonalJournal.forms import RegistrationForm, LogInForm, ToDoForm, UpdateAccountForm, JournalEntryForm, ActivityForm
from flask import request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from PersonalJournal.models import User,Entry, Task, JournalEntry, ActivityEntry
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()


@app.route('/')
@app.route('/Home')
def home():
    if current_user.is_authenticated:
        return render_template('Webpage2.html')
    else:
        return render_template("Webpage1.html") 
@app.route('/About')
def about():
    return render_template('about.html')
@app.route("/Activities", methods=['GET', 'POST'])
@login_required
def acts():
    form = ActivityForm()
    activities = ActivityEntry.query.filter_by(user_id=current_user.id).all()
    if form.validate_on_submit():
        activity = ActivityEntry(title=form.title.data, content=form.content.data, user_id=current_user.id)
        if activity.title and activity.content:
            db.session.add(activity)
            db.session.commit()
            flash('Activity added!', 'success')
            return redirect(url_for('acts'))
        else:
            flash('Try adding title and content!', 'danger')
    return render_template("acts.html", activities=activities, form=form, title='New Activity')
@app.route('/delete_acts/<int:activity_id>', methods=['POST'])
@login_required
def delete_acts(activity_id):
    activity = ActivityEntry.query.get_or_404(activity_id)

    if activity.user_id != current_user.id:
        abort(403)  # Forbidden

    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted!', 'success')
    return redirect(url_for('acts'))
@app.route("/Register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/Login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LogInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/tasks", methods=['GET', 'POST'])
@login_required
def tasks():
    form = ToDoForm()
    
    if form.validate_on_submit():
        new_task = Task(title=form.title.data, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        flash('Task added!', 'success')
        return redirect(url_for('tasks'))

    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("tasks.html", form=form, tasks=tasks)
@app.route("/delete_task/<int:task_id>", methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        abort(403)  # Forbidden

    db.session.delete(task)
    db.session.commit()
    flash('Task deleted!', 'success')
    return redirect(url_for('tasks'))
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/New Folder', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='New Folder/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)
@app.route('/game')
def game():
    return render_template("game.html") 
@app.route('/entries', methods=['GET', 'POST'])
@login_required
def entries():
    form = JournalEntryForm()
    entries = JournalEntry.query.filter_by(user_id=current_user.id).all()
    if form.validate_on_submit():
        entry = JournalEntry(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
        flash('Journal entry created!', 'success')
        return redirect(url_for('entries'))
    return render_template('entries.html', title='New Journal Entry', form=form, entries=entries)
@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)  # Forbidden

    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted!', 'success')
    return redirect(url_for('entries'))
@app.route('/entry/<int:entry_id>')
@login_required
def show_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    return render_template('show_entry.html', entry=entry)

@app.route('/add_friend/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    friend = User.query.get_or_404(friend_id)

    if friend not in current_user.friends:
        current_user.friends.append(friend)
        db.session.commit()
        flash(f"You are now friends with {friend.username}!", "success")
    else:
        flash("You're already friends!", "warning")

    return redirect(url_for('friends'))
@app.route('/friends')
@login_required
def friends():
    return render_template('friends.html', friends=current_user.friends)

@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friend = User.query.get_or_404(friend_id)

    if friend in current_user.friends:
        current_user.friends.remove(friend)
        db.session.commit()
        flash(f"You have removed {friend.username} from your friends.", "info")

    return redirect(url_for('friends'))
@app.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q")  # Get the search query from the form
    if query:
        users = User.query.filter(User.username.ilike(f"%{query}%")).all()  # Case-insensitive search
    else:
        users = []
    return render_template("search.html", users=users, query=query)
@app.route("/calendar")
@login_required
def calendar_view():
    year = request.args.get("year", default=datetime.now().year, type=int)
    month = request.args.get("month", default=datetime.now().month, type=int)
    cal = calendar.monthcalendar(year, month)
    return render_template("calendar.html", cal=cal, year=year, month=month)

@app.route("/entries/<date>")
@login_required
def view_entries(date):
    entries = JournalEntry.query.filter_by(user_id=current_user.id, date=date).all()
    return render_template("entries.html", entries=entries, date=date)

