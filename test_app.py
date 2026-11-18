
"""
Automated feature tests for all 7 pillars.

Run:
python test_app.py
"""

import os
import tempfile
import unittest


# ---------------------------------------------------------
# TEMPORARY TEST DATABASE
# ---------------------------------------------------------

_tmp = tempfile.NamedTemporaryFile(
    suffix='.db',
    delete=False
)

_tmp.close()

os.environ['DATABASE_URL'] = (
    'sqlite:///' + _tmp.name
)


# Import application after setting DATABASE_URL.
import app as hub

from app import (
    app,
    db,
    APIRecord,
    AuditLog,
    User
)


REC = {
    'client_name': 'Equity Bank',
    'api_endpoint': '/api/v1/payments',
    'payload': '{"amount": 1000}',
    'response_sample': '{"status":"success"}'
}


# ---------------------------------------------------------
# AUTOMATED TEST CASES
# ---------------------------------------------------------

class HubTests(unittest.TestCase):

    def setUp(self):

        app.config['TESTING'] = True

        self.c = app.test_client()

        with app.app_context():

            db.create_all()

            APIRecord.query.delete()
            AuditLog.query.delete()

            db.session.commit()

            # Ensure the default admin exists.
            admin = User.query.filter_by(
                username='clare'
            ).first()

            if admin is None:

                from werkzeug.security import generate_password_hash

                admin = User(
                    username='clare',
                    password_hash=generate_password_hash(
                        'Admin2026!'
                    ),
                    role='Lead Developer'
                )

                db.session.add(admin)
                db.session.commit()

    # -----------------------------------------------------
    # HELPER METHODS
    # -----------------------------------------------------

    def login(self, pw='Admin2026!'):

        return self.c.post(
            '/login',
            data={
                'username': 'clare',
                'password': pw
            },
            follow_redirects=True
        )

    def add(self, **kw):

        return self.c.post(
            '/insert',
            data={**REC, **kw},
            follow_redirects=True
        )

    # -----------------------------------------------------
    # PILLAR 7: AUTHENTICATION AND SECURITY
    # -----------------------------------------------------

    def test_7_security_blocks_anonymous(self):

        response = self.c.get('/search')

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/login',
            response.headers['Location']
        )

        response = self.c.post(
            '/insert',
            data=REC
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_7_login_good_and_bad(self):

        response = self.login()

        self.assertIn(
            b'Authentication Successful',
            response.data
        )

        c2 = app.test_client()

        response = c2.post(
            '/login',
            data={
                'username': 'clare',
                'password': 'wrong'
            },
            follow_redirects=True
        )

        self.assertIn(
            b'Invalid Credentials',
            response.data
        )

    def test_7_password_is_hashed(self):

        with app.app_context():

            user = User.query.filter_by(
                username='clare'
            ).first()

            self.assertIsNotNone(user)

            self.assertNotIn(
                'Admin2026!',
                user.password_hash
            )

    # -----------------------------------------------------
    # PILLAR 3: INSERT FUNCTIONALITY
    # -----------------------------------------------------

    def test_3_insert(self):

        self.login()

        response = self.add()

        self.assertIn(
            b'Inserted Successfully',
            response.data
        )

        with app.app_context():

            record = APIRecord.query.first()

            self.assertIsNotNone(record)

            self.assertEqual(
                len(record.sha256_hash),
                64
            )

            self.assertEqual(
                len(record.hmac_signature),
                64
            )

            self.assertEqual(
                AuditLog.query.filter_by(
                    action='INSERT'
                ).count(),
                1
            )

    # -----------------------------------------------------
    # PILLAR 6: UNIQUENESS AND NOVELTY
    # -----------------------------------------------------

    def test_6_duplicate_rejected(self):

        self.login()

        self.add()

        response = self.add()

        self.assertIn(
            b'DUPLICATE ERROR',
            response.data
        )

        with app.app_context():

            self.assertEqual(
                APIRecord.query.count(),
                1
            )

    # -----------------------------------------------------
    # PILLAR 1: SEARCH FUNCTIONALITY
    # -----------------------------------------------------

    def test_1_search(self):

        self.login()

        self.add()

        self.add(
            client_name='KCB Bank',
            api_endpoint='/api/v1/accounts/verify',
            payload='{"account": 12345}'
        )

        response = self.c.get(
            '/search?q=kcb'
        )

        self.assertIn(
            b'KCB Bank',
            response.data
        )

        self.assertNotIn(
            b'Equity Bank',
            response.data
        )

        response = self.c.get(
            '/search?q=payments'
        )

        self.assertIn(
            b'/api/v1/payments',
            response.data
        )

        with app.app_context():

            record = APIRecord.query.filter_by(
                client_name='Equity Bank'
            ).first()

            short_hash = record.sha256_hash[:12]

        response = self.c.get(
            '/search?q=' + short_hash
        )

        self.assertIn(
            b'Equity Bank',
            response.data
        )

    # -----------------------------------------------------
    # PILLAR 2: UPDATE FUNCTIONALITY
    # -----------------------------------------------------

    def test_2_update_recomputes_hash(self):

        self.login()

        self.add()

        with app.app_context():

            record = APIRecord.query.first()

            record_id = record.id
            old_hash = record.sha256_hash

        response = self.c.post(
            f'/update/{record_id}',
            data={
                'client_name': 'Equity Bank',
                'api_endpoint': '/api/v1/payments',
                'payload': '{"amount": 5000}'
            },
            follow_redirects=True
        )

        self.assertIn(
            b'Updated',
            response.data
        )

        with app.app_context():

            record = db.session.get(
                APIRecord,
                record_id
            )

            self.assertNotEqual(
                record.sha256_hash,
                old_hash
            )

            self.assertTrue(
                hub.verify_record(record)
            )

            self.assertEqual(
                AuditLog.query.filter_by(
                    action='UPDATE'
                ).count(),
                1
            )

    def test_2_update_into_duplicate_rejected(self):

        self.login()

        self.add()

        self.add(
            client_name='KCB Bank',
            payload='{"amount": 2000}'
        )

        with app.app_context():

            record = APIRecord.query.filter_by(
                client_name='KCB Bank'
            ).first()

            record_id = record.id

        response = self.c.post(
            f'/update/{record_id}',
            data={
                'client_name': REC['client_name'],
                'api_endpoint': REC['api_endpoint'],
                'payload': REC['payload']
            },
            follow_redirects=True
        )

        self.assertIn(
            b'DUPLICATE ERROR',
            response.data
        )

        with app.app_context():

            self.assertEqual(
                APIRecord.query.count(),
                2
            )

    # -----------------------------------------------------
    # PILLAR 4: DELETE FUNCTIONALITY
    # -----------------------------------------------------

    def test_4_delete_and_audit(self):

        self.login()

        self.add()

        with app.app_context():

            record_id = APIRecord.query.first().id

        response = self.c.post(
            f'/delete/{record_id}',
            follow_redirects=True
        )

        self.assertIn(
            b'Deleted',
            response.data
        )

        with app.app_context():

            self.assertEqual(
                APIRecord.query.count(),
                0
            )

            self.assertEqual(
                AuditLog.query.filter_by(
                    action='DELETE'
                ).count(),
                1
            )

    # -----------------------------------------------------
    # PILLAR 5: CRYPTOGRAPHIC INTEGRITY
    # -----------------------------------------------------

    def test_5_tamper_detected(self):

        self.login()

        self.add()

        with app.app_context():

            record = APIRecord.query.first()

            self.assertTrue(
                hub.verify_record(record)
            )

            record.request_payload = (
                '{"amount": 999999}'
            )

            db.session.commit()

            self.assertFalse(
                hub.verify_record(
                    APIRecord.query.first()
                )
            )

        response = self.c.get('/search')

        self.assertIn(
            b'TAMPERED',
            response.data
        )

    # -----------------------------------------------------
    # DASHBOARD AND LOGOUT
    # -----------------------------------------------------

    def test_dashboard_and_logout(self):

        self.login()

        self.add()

        response = self.c.get('/')

        self.assertIn(
            b'Integrity Verified',
            response.data
        )

        response = self.c.get(
            '/logout',
            follow_redirects=True
        )

        self.assertIn(
            b'Logged Out',
            response.data
        )

        response = self.c.get('/')

        self.assertEqual(
            response.status_code,
            302
        )


# ---------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------

if __name__ == '__main__':

    unittest.main(verbosity=2)
