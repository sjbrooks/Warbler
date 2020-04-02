"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warbler_test'

from app import app


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u1 = User(
            email="user1@test.com",
            username="testuserONE",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)

        u2 = User(
            email="user2@test.com",
            username="testuserTWO",
            password="HASHED_PASSWORD"
        )

        db.session.add(u2)
        db.session.commit()

        self.user1_id = u1.id
        self.user2_id = u2.id

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_user_model(self):
        """Does basic model work?"""

        test_user1 = User.query.get(self.user1_id)

        # User should have no messages & no followers
        self.assertEqual(len(test_user1.messages), 0)
        self.assertEqual(len(test_user1.followers), 0)

    def test_repr_model(self):
        """ makes sure our repr returns the correct information about user """

        test_user1 = User.query.get(self.user1_id)

        self.assertEqual(
            f"{test_user1}", f"<User #{test_user1.id}: {test_user1.username}, {test_user1.email}>")

    def test_is_following(self):
        """ test to see if user following another user is successfully detected"""

        test_user1 = User.query.get(self.user1_id)
        test_user2 = User.query.get(self.user2_id)

        test_user1.following.append(test_user2)
        db.session.commit()

        self.assertEqual(test_user1.following[0].id, test_user2.id)

        test_user1.following.pop()
        db.session.commit()

        self.assertNotEqual(test_user1.following, test_user2)

    def test_is_followed_by(self):
        """ test to see if  user followers are successfully recorded"""

        test_user1 = User.query.get(self.user1_id)
        test_user2 = User.query.get(self.user2_id)

        test_user1.followers.append(test_user2)
        db.session.commit()

        self.assertEqual(test_user1.followers[0].id, test_user2.id)

        test_user1.followers.pop()
        db.session.commit()

        self.assertNotEqual(test_user1.followers, test_user1)

    def test_user_create(self):
        """ tests user creation """

        new_user = User(email="test3@test.com",
                        username="jim", password="secret")

        db.session.add(new_user)
        db.session.commit()

        self.assertIsInstance(new_user, User)
        self.assertEqual(
            f"{new_user}", f"<User #{new_user.id}: {new_user.username}, {new_user.email}>")

        invalid_user = User(email="user2@test.com",
                            username="jim", password="mypassword")
        db.session.add(invalid_user)

        # as explained by joel in lecture, imported exc from sqlalchemy
        # and used assert Raises to expect the integrity error method from exc

        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

