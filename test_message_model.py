"""Message model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest <name-of-python-file>


from app import app
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


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Testcase for Message model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u1 = User.signup("testuserONE", "user1@test.com",
                         "HASHED_PASSWORD", None)
        db.session.add(u1)
        db.session.commit()

        u2 = User.signup("testuserTWO", "user2@test.com",
                         "HASHED_PASSWORD", None)
        db.session.add(u2)
        db.session.commit()

        m1 = Message(text="Text Test", timestamp=None, user_id=u1.id)
        # u1.messages.append(m1)
        db.session.add(m1)
        db.session.commit()

        self.user1_id = u1.id
        self.user2_id = u2.id
        self.msg_id = m1.id

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_message_model(self):
        """Test that the model works"""
        test_user1 = User.query.get(self.user1_id)
        messages = test_user1.messages
        self.assertEqual(self.msg_id, messages[0].id)

    def test_repr_model(self):
        """Test that the repr returns the expected format and data"""
        test_user1 = User.query.get(self.user1_id)
        message = test_user1.messages[0]

        self.assertEqual(
            f"{message}", f"<Message #{message.id}: {message.text}, {message.timestamp}, {message.user_id}>")

    def test_create_message(self):
        """Tests that we can create a new message 
        instance and add it to the database"""

        m = Message(text="Testing Testing",
                    timestamp=None, 
                    user_id=self.user1_id)
        db.session.add(m)
        db.session.commit()

        test_user1 = User.query.get(self.user1_id)
        messages = test_user1.messages

        print("\n\n\n THE MESSAGES LIST IS", messages, "\n\n\n")

        self.assertEqual(len(messages), 2)
        self.assertEqual(f"{messages[1]}", f"<Message #{m.id}: {m.text}, {m.timestamp}, {m.user_id}>")


    ### Liking and unliking, deleting
