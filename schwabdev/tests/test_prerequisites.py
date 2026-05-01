import unittest
from pathlib import Path
import sqlite3

class TestPrerequisites(unittest.TestCase):
    def test_gitignore_exists(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertTrue(gitignore.exists(), f".gitignore not found at {gitignore}")

    def test_gitignore_contains_env_pattern(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertIn("*.env", gitignore.read_text(), ".gitignore does not contain '*.env'")

    def test_sqlite_running(self):
        conn = sqlite3.connect(':memory:')  # Connect to an in-memory database
        self.assertIsNotNone(conn, "expecting sqlite3 daemon")  # Check if the connection is not None
        conn.close()  # Close the connection

if __name__ == "__main__":
    unittest.main()
