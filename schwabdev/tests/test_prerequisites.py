import unittest
from pathlib import Path


class TestPrerequisites(unittest.TestCase):
    def test_gitignore_exists(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertTrue(gitignore.exists(), f".gitignore not found at {gitignore}")

    def test_gitignore_contains_env_pattern(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertIn("*.env", gitignore.read_text(), ".gitignore does not contain '*.env'")


if __name__ == "__main__":
    unittest.main()
