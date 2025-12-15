#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the Flask application."""
import os
from datetime import datetime
from app import create_app, db

app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.context_processor
def inject_now():
    """Inject current datetime into templates."""
    return {'now': datetime.now}


@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database tables created.')


@app.cli.command('create-user')
def create_user():
    """Create a test user."""
    from app.models import User

    username = input('Username: ')
    email = input('Email: ')
    password = input('Password: ')

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print(f'User {username} created successfully.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
