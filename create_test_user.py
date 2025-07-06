from db import db
from app import app
from models import User

with app.app_context():
    db.drop_all()
    db.create_all()
    # Create test employee
    if not User.query.filter_by(username='testuser').first():
        user = User(username='testuser', password='testpass', email='testuser@example.com', is_admin=False)
        db.session.add(user)
        print('Test employee created.')
    else:
        print('Test employee already exists.')
    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='adminpass', email='admin@example.com', is_admin=True)
        db.session.add(admin)
        print('Admin user created.')
    else:
        print('Admin user already exists.')
    db.session.commit() 