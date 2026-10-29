import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))
import app as gateway

class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.saved = dict(gateway.app.config)
        self.addCleanup(lambda: gateway.app.config.update(self.saved))
        gateway.app.config.update(TESTING=True, SECRET_KEY='test-secret',
                                 ADMIN_PASSWORD='test-password', SESSION_COOKIE_SECURE=True)
        gateway.login_attempts.clear()
        self.production = patch.object(gateway, 'IS_PRODUCTION', True)
        self.origin = patch.object(gateway, 'PUBLIC_ORIGIN', 'https://portfolio.example')
        self.production.start(); self.origin.start()
        self.addCleanup(self.production.stop); self.addCleanup(self.origin.stop)
        self.client = gateway.app.test_client()

    def post(self, path, **kwargs):
        return self.client.post(path, base_url='https://portfolio.example', **kwargs)

    def test_cross_origin_and_missing_origin_login_rejected(self):
        for headers in ({}, {'Origin':'https://attacker.example'}):
            self.assertEqual(self.post('/api/login', headers=headers,
                             json={'password':'test-password'}).status_code,403)

    def test_login_cookie_and_logout(self):
        headers={'Origin':'https://portfolio.example'}
        response=self.post('/api/login',headers=headers,json={'password':'test-password'})
        self.assertEqual(response.status_code,200)
        cookie=response.headers['Set-Cookie']
        for flag in ['Secure','HttpOnly','SameSite=Lax']: self.assertIn(flag,cookie)
        self.assertTrue(self.client.get('/api/session-check',base_url='https://portfolio.example').json['is_admin'])
        self.assertEqual(self.post('/api/logout',headers=headers).status_code,200)
        self.assertFalse(self.client.get('/api/session-check',base_url='https://portfolio.example').json['is_admin'])

    def test_rotation_requires_admin_before_touching_database(self):
        with patch('routes.admin_photography.sqlite3.connect') as connect:
            self.assertEqual(self.post('/api/photography/rotate',
                headers={'Origin':'https://portfolio.example'},json={'limit':3}).status_code,403)
            connect.assert_not_called()

    def test_login_throttled(self):
        for _ in range(5):
            self.assertEqual(self.post('/api/login',headers={'Origin':'https://portfolio.example'},
                json={'password':'incorrect'}).status_code,401)
        self.assertEqual(self.post('/api/login',headers={'Origin':'https://portfolio.example'},
            json={'password':'incorrect'}).status_code,429)

    def failed_login(self, remote_addr, real_ip=None):
        headers = {'Origin':'https://portfolio.example'}
        if real_ip: headers['X-Real-IP'] = real_ip
        return self.post('/api/login', headers=headers, json={'password':'incorrect'},
                         environ_base={'REMOTE_ADDR':remote_addr}).status_code

    def test_login_limit_is_per_visitor_behind_the_proxy(self):
        # PythonAnywhere's balancer connects from a private address and names the visitor.
        # (Real public addresses: Python counts the documentation example ranges as private.)
        for _ in range(5): self.assertEqual(self.failed_login('10.0.0.7', '81.2.69.160'), 401)
        self.assertEqual(self.failed_login('10.0.0.7', '81.2.69.160'), 429)
        self.assertEqual(self.failed_login('10.0.0.7', '8.8.4.4'), 401)

    def test_visitor_cannot_choose_their_address_directly(self):
        # A public connection's own X-Real-IP is ignored, so changing it doesn't reset the limit.
        for n in range(5): self.assertEqual(self.failed_login('81.2.69.160', f'1.1.1.{n}'), 401)
        self.assertEqual(self.failed_login('81.2.69.160', '1.1.1.99'), 429)

    def test_malformed_proxy_header_falls_back_to_connection(self):
        with gateway.app.test_request_context(headers={'X-Real-IP':'not-an-ip'},
                                              environ_base={'REMOTE_ADDR':'10.0.0.7'}):
            self.assertEqual(gateway.client_address(), '10.0.0.7')
        with gateway.app.test_request_context(environ_base={'REMOTE_ADDR':'10.0.0.7'}):
            self.assertEqual(gateway.client_address(), '10.0.0.7')

    def test_public_static_and_private_paths(self):
        for path in ['/', '/bio.html','/resume.html','/math/','/runtime-config.js']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200,path)
            response.close()
        for path in ['/backend/portfolio.db','/.git/config','/../backend/portfolio.db','/api/not-a-route']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,404,path)
            response.close()

    def test_production_rejects_missing_secrets(self):
        env=dict(os.environ,FLASK_ENV='production',PUBLIC_ORIGIN='https://portfolio.example')
        env.pop('ADMIN_PASSWORD',None);env.pop('FLASK_SECRET_KEY',None)
        result=subprocess.run([sys.executable,'-c','import app'],cwd=SRC,env=env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'Production requires',result.stderr)

if __name__=='__main__':unittest.main()
