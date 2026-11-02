"""
SpamGuard AI - End-to-End Authentication & System Verification
Tests registration, duplicate checks, login, token authentication,
protected user routes, logout, Gmail OAuth separation, and ML services.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import create_app
from database import db
from models import User

def main():
    print("\n" + "=" * 70)
    print("  🧪 SpamGuard AI — Complete Authentication & System Audit")
    print("=" * 70)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # ── Test 1: User Registration Validations ─────────────────────
        print("\n[1/6] Testing User Registration...")
        
        # Missing fields
        r_empty = client.post('/api/auth/register', json={})
        assert r_empty.status_code == 400, f"Expected 400, got {r_empty.status_code}"
        print(f"  ✅ Empty payload rejected: {r_empty.get_json()['message']}")

        # Short password
        r_short = client.post('/api/auth/register', json={'name': 'Jane Doe', 'email': 'jane@spamguard.io', 'password': '123'})
        assert r_short.status_code == 400, f"Expected 400, got {r_short.status_code}"
        print(f"  ✅ Short password rejected: {r_short.get_json()['message']}")

        # Valid registration
        test_email = 'analyst@spamguard.io'
        # Clean up if already exists from earlier test
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        r_reg = client.post('/api/auth/register', json={
            'name': 'Security Analyst',
            'email': test_email,
            'password': 'StrongPassword2026!'
        })
        assert r_reg.status_code == 201, f"Expected 201, got {r_reg.status_code}"
        user_data = r_reg.get_json()['data']['user']
        assert user_data['email'] == test_email
        assert user_data['has_password'] is True
        print(f"  ✅ User registration successful: {user_data['name']} ({user_data['email']})")

        # Duplicate email check
        r_dup = client.post('/api/auth/register', json={
            'name': 'Duplicate User',
            'email': test_email,
            'password': 'AnotherPassword!'
        })
        assert r_dup.status_code == 400
        print(f"  ✅ Duplicate registration prevented: {r_dup.get_json()['message']}")

        # ── Test 2: User Sign In & Credential Checks ─────────────────
        print("\n[2/6] Testing User Sign In...")

        # Wrong password
        r_wrong = client.post('/api/auth/user/login', json={
            'email': test_email,
            'password': 'IncorrectPassword!'
        })
        assert r_wrong.status_code == 401
        print(f"  ✅ Invalid password rejected: {r_wrong.get_json()['message']}")

        # Correct login
        r_login = client.post('/api/auth/user/login', json={
            'email': test_email,
            'password': 'StrongPassword2026!',
            'remember': True
        })
        assert r_login.status_code == 200
        login_res = r_login.get_json()['data']
        token = login_res['token']
        assert bool(token)
        print(f"  ✅ Sign In successful! Generated Bearer token: {token[:25]}... (User: {login_res['user']['name']})")

        # Also test dual-mode /api/auth/login (POST)
        r_dual_login = client.post('/api/auth/login', json={
            'email': test_email,
            'password': 'StrongPassword2026!'
        })
        assert r_dual_login.status_code == 200
        print(f"  ✅ Dual-mode POST /api/auth/login also works: {r_dual_login.get_json()['message']}")

        # ── Test 3: Session & Protected Route Verification ───────────
        print("\n[3/6] Testing Authentication Persistence & Protected Routes...")

        # Fresh unauthenticated client without session cookie
        fresh_client = app.test_client()
        r_unauth = fresh_client.get('/api/auth/user/me')
        assert r_unauth.get_json()['data']['authenticated'] is False
        print("  ✅ Unauthenticated user request correctly returns authenticated=False")

        # Authenticated /api/auth/user/me with Bearer token
        r_auth = client.get('/api/auth/user/me', headers={'Authorization': f'Bearer {token}'})
        assert r_auth.status_code == 200
        auth_data = r_auth.get_json()['data']
        assert auth_data['authenticated'] is True
        assert auth_data['user']['email'] == test_email
        print(f"  ✅ Authenticated session verified: {auth_data['user']['name']} ({auth_data['user']['email']})")

        # ── Test 4: Sign Out ─────────────────────────────────────────
        print("\n[4/6] Testing Sign Out...")
        r_logout = client.post('/api/auth/user/logout')
        assert r_logout.status_code == 200
        print(f"  ✅ Sign out endpoint confirmed: {r_logout.get_json()['message']}")

        # ── Test 5: Gmail OAuth System Separation ────────────────────
        print("\n[5/6] Verifying Gmail OAuth System Independence...")

        # Check that Google OAuth status is untouched
        r_oauth_status = client.get('/api/auth/status')
        assert r_oauth_status.status_code == 200
        oauth_data = r_oauth_status.get_json()['data']
        print(f"  ✅ Google OAuth Status endpoint intact: connected={oauth_data.get('connected')}")

        # Check Google OAuth login URL generator (GET)
        r_oauth_url = client.get('/api/auth/login')
        assert r_oauth_url.status_code == 200
        assert 'oauth_url' in r_oauth_url.get_json()['data']
        print("  ✅ Google OAuth GET /api/auth/login URL generator intact")

        # ── Test 6: ML & Dashboard Integration ───────────────────────
        print("\n[6/6] Verifying ML Models & Dashboard Services...")
        r_perf = client.get('/api/models/performance')
        assert r_perf.status_code == 200
        perf_data = r_perf.get_json()['data']
        assert perf_data.get('active_version') == 'v7'
        assert perf_data.get('dataset', {}).get('total_samples') == 30462
        print(f"  ✅ ML Model Performance intact: Version={perf_data.get('active_version')}, Samples={perf_data.get('dataset', {}).get('total_samples'):,}")

        r_stats = client.get('/api/dashboard/stats')
        assert r_stats.status_code == 200
        stats_data = r_stats.get_json()['data']
        total_scanned = stats_data.get('total_emails_scanned', 0)
        print(f"  ✅ Dashboard stats API intact: Total emails scanned={total_scanned:,}")

    print("\n" + "=" * 70)
    print("  🎉 ALL 6 TEST SUITES PASSED WITH ZERO ERRORS!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
