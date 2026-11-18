
"""
API Communication Records Management System
For Embu Developers Hub

Student Name: Clare Wambui
Registration Number: dse-02-8535/2024
Institution: Zetech University
"""

import os
import hashlib
import hmac
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------
# APPLICATION CONFIGURATION
# ---------------------------------------------------------

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'EmbuDevHub_SecureKey_2026_ClareWambui'
)

# Allow tests to use their own temporary database.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///api_records.db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# HMAC secret key for cryptographic integrity verification.
HMAC_SECRET_KEY = b'Embu_Dev_Hub_HMAC_Integrity_Secret_2026'


# ---------------------------------------------------------
# DATABASE MODELS
# ---------------------------------------------------------

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(256),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        default='Staff Officer'
    )


class APIRecord(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    client_name = db.Column(
        db.String(120),
        nullable=False
    )

    api_endpoint = db.Column(
        db.String(200),
        nullable=False
    )

    request_payload = db.Column(
        db.Text,
        nullable=False
    )

    response_sample = db.Column(
        db.Text,
        nullable=True
    )

    sha256_hash = db.Column(
        db.String(64),
        unique=True,
        nullable=False
    )

    hmac_signature = db.Column(
        db.String(64),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default='Active'
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )


class AuditLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    action = db.Column(
        db.String(50),
        nullable=False
    )

    details = db.Column(
        db.Text,
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    integrity_status = db.Column(
        db.String(20),
        default='VERIFIED'
    )


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def compute_cryptographic_hashes(
    client_name,
    api_endpoint,
    payload
):
    """
    Calculate SHA-256 and HMAC-SHA256 hashes.
    Used for uniqueness and integrity verification.
    """

    raw_content = (
        f"{client_name.strip()}:"
        f"{api_endpoint.strip()}:"
        f"{payload.strip()}"
    )

    sha256_digest = hashlib.sha256(
        raw_content.encode('utf-8')
    ).hexdigest()

    hmac_signature = hmac.new(
        HMAC_SECRET_KEY,
        sha256_digest.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return sha256_digest, hmac_signature


def verify_record(rec):
    """
    Verify the integrity of a stored API record.
    Returns False if the record has been modified.
    """

    sha, signature = compute_cryptographic_hashes(
        rec.client_name,
        rec.api_endpoint,
        rec.request_payload
    )

    return (
        hmac.compare_digest(sha, rec.sha256_hash)
        and
        hmac.compare_digest(
            signature,
            rec.hmac_signature
        )
    )


def validate_record_input(client_name, endpoint, payload):
    """
    Validate required record fields.
    """

    if not all([
        client_name,
        endpoint,
        payload
    ]):
        return False

    if not client_name.strip():
        return False

    if not endpoint.strip():
        return False

    if not payload.strip():
        return False

    return True


# Make integrity verification available in HTML templates.
app.jinja_env.globals['is_verified'] = verify_record


# ---------------------------------------------------------
# LOGIN MANAGEMENT
# ---------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


# ---------------------------------------------------------
# DATABASE INITIALIZATION AND DEFAULT ADMIN
# ---------------------------------------------------------

def initialize_database():

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(
            username='clare'
        ).first()

        if admin is None:

            hashed_password = generate_password_hash(
                'Admin2026!'
            )

            admin = User(
                username='clare',
                password_hash=hashed_password,
                role='Lead Developer'
            )

            db.session.add(admin)
            db.session.commit()


# ---------------------------------------------------------
# PILLAR 7: AUTHENTICATION AND SECURITY
# ---------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get(
            'username', ''
        ).strip()

        password = request.form.get(
            'password', ''
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if (
            user
            and check_password_hash(
                user.password_hash,
                password
            )
        ):

            login_user(user)

            flash(
                "Authentication Successful. "
                "Welcome to Embu Dev Hub Portal.",
                "success"
            )

            return redirect(url_for('dashboard'))

        flash(
            "Invalid Credentials. Please check Officer ID and Password.",
            "danger"
        )

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash(
        "Successfully Logged Out.",
        "info"
    )

    return redirect(url_for('login'))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route('/')
@login_required
def dashboard():

    all_records = APIRecord.query.all()

    total_records = len(all_records)

    verified_count = sum(
        1 for record in all_records
        if verify_record(record)
    )

    audit_count = AuditLog.query.count()

    recent_records = APIRecord.query.order_by(
        APIRecord.created_at.desc()
    ).limit(5).all()

    recent_audits = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).limit(6).all()

    if verified_count == total_records:
        flash(
            "Integrity Verified: All API records passed verification.",
            "success"
        )
    else:
        flash(
            "WARNING: TAMPERED API RECORDS DETECTED.",
            "danger"
        )

    return render_template(
        'dashboard.html',
        total_records=total_records,
        verified_count=verified_count,
        audit_count=audit_count,
        records=recent_records,
        audits=recent_audits
    )


# ---------------------------------------------------------
# PILLAR 1: SEARCH FUNCTIONALITY
# ---------------------------------------------------------

@app.route('/search', methods=['GET'])
@login_required
def search():

    query = request.args.get(
        'q', ''
    ).strip()

    if query:

        results = APIRecord.query.filter(
            (APIRecord.client_name.ilike(f'%{query}%')) |
            (APIRecord.api_endpoint.ilike(f'%{query}%')) |
            (APIRecord.sha256_hash.ilike(f'%{query}%'))
        ).all()

    else:

        results = APIRecord.query.all()

    # Detect records whose integrity has been compromised.
    tampered_records = [
        record for record in results
        if not verify_record(record)
    ]

    if tampered_records:

        flash(
            "TAMPERED RECORD DETECTED: "
            "One or more API records have been modified.",
            "danger"
        )

    return render_template(
        'inventory.html',
        records=results,
        query=query
    )


# ---------------------------------------------------------
# PILLAR 3: INSERT API RECORDS
# ---------------------------------------------------------

@app.route('/insert', methods=['POST'])
@login_required
def insert():

    client_name = request.form.get(
        'client_name', ''
    )

    endpoint = request.form.get(
        'api_endpoint', ''
    )

    payload = request.form.get(
        'payload', ''
    )

    response_sample = request.form.get(
        'response_sample', '{}'
    )

    # Validate input before calculating hashes.
    if not validate_record_input(
        client_name,
        endpoint,
        payload
    ):

        flash(
            "ERROR: All required API record fields must be provided.",
            "danger"
        )

        return redirect(url_for('search'))

    sha256_digest, hmac_signature = (
        compute_cryptographic_hashes(
            client_name,
            endpoint,
            payload
        )
    )

    # Pillar 6: Check uniqueness.
    existing = APIRecord.query.filter_by(
        sha256_hash=sha256_digest
    ).first()

    if existing:

        flash(
            f"DUPLICATE ERROR: API Payload already exists "
            f"for client '{existing.client_name}'. Entry rejected!",
            "danger"
        )

        return redirect(url_for('search'))

    new_record = APIRecord(
        client_name=client_name.strip(),
        api_endpoint=endpoint.strip(),
        request_payload=payload,
        response_sample=response_sample,
        sha256_hash=sha256_digest,
        hmac_signature=hmac_signature,
        user_id=current_user.id
    )

    audit = AuditLog(
        action="INSERT",
        details=(
            f"Inserted API Record for "
            f"{client_name} ({endpoint})"
        )
    )

    try:

        db.session.add(new_record)
        db.session.add(audit)
        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "ERROR: Unable to insert API record.",
            "danger"
        )

        return redirect(url_for('search'))

    flash(
        "API Communication Record Inserted Successfully "
        "with SHA-256 Verification!",
        "success"
    )

    return redirect(url_for('search'))


# ---------------------------------------------------------
# PILLAR 2: UPDATE API RECORDS
# ---------------------------------------------------------

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):

    record = APIRecord.query.get_or_404(id)

    client_name = request.form.get(
        'client_name', ''
    )

    endpoint = request.form.get(
        'api_endpoint', ''
    )

    payload = request.form.get(
        'payload', ''
    )

    if not validate_record_input(
        client_name,
        endpoint,
        payload
    ):

        flash(
            "ERROR: All required fields must be provided.",
            "danger"
        )

        return redirect(url_for('search'))

    # Recalculate hashes.
    new_sha, new_signature = compute_cryptographic_hashes(
        client_name,
        endpoint,
        payload
    )

    # Prevent updating a record into an existing duplicate.
    duplicate = APIRecord.query.filter(
        APIRecord.sha256_hash == new_sha,
        APIRecord.id != record.id
    ).first()

    if duplicate:

        flash(
            "DUPLICATE ERROR: Updated API record already exists. "
            "Update rejected!",
            "danger"
        )

        return redirect(url_for('search'))

    record.client_name = client_name.strip()
    record.api_endpoint = endpoint.strip()
    record.request_payload = payload

    record.sha256_hash = new_sha
    record.hmac_signature = new_signature

    audit = AuditLog(
        action="UPDATE",
        details=(
            f"Updated API ID {record.id} "
            f"for {record.client_name}"
        )
    )

    try:

        db.session.add(audit)
        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "ERROR: Unable to update API record.",
            "danger"
        )

        return redirect(url_for('search'))

    flash(
        "API Record Updated Successfully. "
        "Cryptographic Hashes Re-verified!",
        "success"
    )

    return redirect(url_for('search'))


# ---------------------------------------------------------
# PILLAR 4: DELETE API RECORDS
# ---------------------------------------------------------

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):

    record = APIRecord.query.get_or_404(id)

    audit = AuditLog(
        action="DELETE",
        details=(
            f"Deleted API ID {record.id} "
            f"({record.client_name} - {record.api_endpoint})"
        )
    )

    try:

        db.session.add(audit)
        db.session.delete(record)
        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "ERROR: Unable to delete API record.",
            "danger"
        )

        return redirect(url_for('search'))

    flash(
        "API Record Deleted and Logged in System Audit Trail.",
        "warning"
    )

    return redirect(url_for('search'))


# ---------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------

# Initialize tables and admin when the application is imported.
initialize_database()


if __name__ == '__main__':

    app.run(debug=True)
