"""Every response carries the security headers set in the app factory."""

from main import app


def test_security_headers_on_every_response():
    app.config['TESTING'] = True
    with app.test_client() as client:
        for path in ('/', '/login', '/no-such-page'):
            response = client.get(path)
            csp = response.headers['Content-Security-Policy']
            assert "default-src 'self'" in csp
            assert "frame-ancestors 'none'" in csp
            assert response.headers['X-Frame-Options'] == 'DENY'
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
