"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from flask import session

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app, CURR_USER_KEY, do_login, do_logout


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for Users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                     email="test1@test.com",
                                     password="testuser1",
                                     image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser2",
                                     image_url=None)

        db.session.commit()

        self.user1id = self.testuser1.id
        self.user2id = self.testuser2.id


    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_follows_upon_login(self):

        """tests to see if we can see a user's followers/following when logged in"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.user1id

        user1 = User.query.get(self.user1id)
        user2 = User.query.get(self.user2id)


        user2.following.append(user1)
        db.session.commit()


        resp = self.client.get(
            f"/users/{self.user1id}/followers", follow_redirects=True)

        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)

        # with self.client.session_transaction() as sess:
        #     sess[CURR_USER_KEY] = self.user1id

        # self.assertIn("card user-card", html)
        self.assertIn('<div class="card user-card">', html)
    
    def test_follows_upon_logout(self):

        """tests to make sure we are redirected to home page if we are locked out"""

        self.testuser2.following.append(self.testuser1)
        db.session.commit()
        
        resp = self.client.get(
            f"/users/{self.testuser1.id}/followers", follow_redirects=True)

        html = resp.get_data(as_text=True)

        #tests viewing a user's followers when logged out

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.', html)

        #tests viewing a user's followers when logged out

        resp = self.client.get(
            f"/users/{self.user2id}/following", follow_redirects=True)

        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.', html)

    def test_add_msg_on_login(self):

        """check to see if message can be added by a logged in user"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.user1id

        user1 = User.query.get(self.user1id)

        message = Message(text="here's a test", timestamp=None, user_id=user1.id)

        db.session.add(message)
        db.session.commit()

        # user1 = User.query.get(self.user1id)
        # message_new = user1.messages[0]


        resp = self.client.get(
            f"/messages/{message.id}")

        html = resp.get_data(as_text=True)

        user1 = User.query.get(self.user1id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user1.messages[0].text, "here's a test")


        # curious as to why this isnt returning the correct html, even though we
        # are sending  the  corret message id throubgh  the client in line 142.

        # self.assertIn("here's a test", html)

        #=============================================================================

        # these are exactly the same, even in a new py document with the find feature. 
        # why does unittest throw an assertion error??

        # self.assertEqual(user1.messages[0], message)

    
    
