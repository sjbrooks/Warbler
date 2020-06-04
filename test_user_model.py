"""User model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest <name-of-python-file>


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, we need to set an environmental variable
# to use a different database for tests

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app, do_login, do_logout


db.create_all()


class UserModelTestCase(TestCase):
    """Test case for User model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u1 = User.signup("testuserONE", "user1@test.com", "HASHED_PASSWORD", "")

        db.session.add(u1)

        u2 = User.signup("testuserTWO", "user2@test.com", "HASHED_PASSWORD", "")

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

        self.assertEqual(f"{test_user1}", f"<User #{test_user1.id}: {test_user1.username}, {test_user1.email}>")

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

        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_user_authenticate(self):
        """Tests that valid authentication works"""

        test_user1 = User.query.get(self.user1_id)
        res = User.authenticate(test_user1.username, "HASHED_PASSWORD")

        self.assertEqual(res, test_user1)
        self.assertNotEqual(res, False)

        res2 = User.authenticate('NonExistantUsername', "HASHED_PASSWORD")
        self.assertEqual(res2, False)


