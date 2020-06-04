# Warbler

Twitter clone, fullstack Python app with Flask backend, PostgreSQL database, and Jinja-based templating for the frontend.

I built off of a somewhat functional clone to implement new features, including:
  - The logout route with succes/failure alerts
  - An updated user profile and user card UI to show the user's info and image
  - Routes and a form to give logged in users the ability to edit their profile
  - An updated homepage query to show only the most recent 100 warbles from users that the user is following
  - The ability to like and dislike messages
  - Unit tests for the models
  - Integration tests for the views


# Getting Started

1. Clone the repository
2. Create your python virtual environment
    - `python3 -m venv venv`
    - `source venv/bin/activate`
    - `pip install -r requirements.txt`
3. Set up the database
    - `createdb warbler`
    - `python seed.py`
4. Start the server: `flask run`


## Built With

* [Flask](https://flask.palletsprojects.com/en/1.1.x/) - Web framework
* [bcrypt](https://www.npmjs.com/package/bcrypt) - Cryptographic hashing for passwords
* [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit and object relational mapper
* [WTForms](https://wtforms.readthedocs.io/en/stable/) - forms rendering and validation library
* [Jinja](https://jinja.palletsprojects.com/en/2.11.x/) - Python-based templating language


## Authors

* My pair for this project was @gladkillmusic


## Acknowledgments

* The goal of this assignment was to practice working in a new codebase that we didn't write. The features we implemented were built on top of [this](http://curric.rithmschool.com/r15/exercises/warbler.zip) original, somewhat functional Twitter clone.
