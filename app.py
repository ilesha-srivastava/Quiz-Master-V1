# task of app.py - initial setup of the app

from flask import Flask, session
# to import/acccess all the routes from controllers.py file
#  from controllers.controllers import *                - importing here causes circular import
# Importing the database and User model
from models.models import db, User
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure and random value
# database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///quiz_master.sqlite3"
db.init_app(app)        # Flask app is connected to DB(SQL alchemy)


def create_admin():
    with app.app_context():
        admin_exists = User.query.filter_by(username="admin@gmail.com").first()
        if not admin_exists:
            # Creating new user with hardcoded details
            admin_user = User(
                fullname = "Admin",
                username = "admin@gmail.com",
                password = generate_password_hash("admin123"),   
                role = "ADMIN",
                dob = "2000-01-01",
                qualification = "N/A"
            )
            # Adding the user to the session and commiting to add the user to the database
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")


# to get the direct access to other modules
# app.app_context().push()          
with app.app_context():
    db.create_all()  # Create tables if they don’t exist
    create_admin()   # Call function to create admin user


from controllers.controllers import *   # importing all the routes from controllers.py file

# Running the app
if __name__ == '__main__':          # even after removing if condition the app works
    app.run(debug=True)

