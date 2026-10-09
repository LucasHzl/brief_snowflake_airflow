"""Check local connection file handling without using real credentials."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ConfigureAirflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'ingestion').mkdir()
        (self.root / 'airflow').mkdir()
        self.script = self.root / 'ingestion/configure_airflow.py'
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'ingestion/configure_airflow.py', self.script)
        self.key = self.root / 'key.p8'
        # This tests configuration serialization, not cryptographic authentication.
        self.key.write_text('-----BEGIN PRIVATE KEY-----\nTEST_ONLY\n-----END PRIVATE KEY-----\n')

    def run_command(self):
        return subprocess.run([sys.executable, str(self.script), '--account', 'TEST-ACCOUNT',
                               '--private-key', str(self.key)], text=True, capture_output=True)

    def test_serialization_permissions_and_no_secret_output(self):
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / 'airflow/.env'
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        payload = output.read_text().strip().split('=', 1)[1][1:-1]
        self.assertEqual(json.loads(payload)['extra']['private_key_content'], self.key.read_text())
        self.assertNotIn('TEST_ONLY', result.stdout + result.stderr)

    def test_existing_file_is_preserved(self):
        output = self.root / 'airflow/.env'
        output.write_text('existing configuration\n')
        self.assertNotEqual(self.run_command().returncode, 0)
        self.assertEqual(output.read_text(), 'existing configuration\n')

    def test_invalid_key_creates_no_file(self):
        self.key.write_text('invalid key')
        self.assertNotEqual(self.run_command().returncode, 0)
        self.assertFalse((self.root / 'airflow/.env').exists())


if __name__ == '__main__':
    unittest.main()
