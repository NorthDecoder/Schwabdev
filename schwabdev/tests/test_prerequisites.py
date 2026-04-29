import unittest
from pathlib import Path


class TestPrerequisites(unittest.TestCase):
    def test_gitignore_exists(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertTrue(gitignore.exists(), f".gitignore not found at {gitignore}")


if __name__ == "__main__":
    unittest.main()
