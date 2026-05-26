from dotenv import dotenv_values
from dotenv import set_key
from dotenv import unset_key
from pathlib import Path    # manage paths
import sqlite3
import unittest

class TestPrerequisites(unittest.TestCase):

    def get_path_of_dot_env(self):
        # define where the file will be
        return Path(__file__).resolve().parents[2] / ".env"

    @classmethod
    def setUpClass(self):
        dep = self.get_path_of_dot_env(self)
        if dep.exists():
            #print("The .env file already exists, no need to create")
            pass
        else:
            # create file
            dep.touch(exist_ok=False)

        # add example variables
        set_key(dotenv_path=dep, key_to_set="test_app_key", value_to_set="your_app_key_here")
        set_key(dotenv_path=dep, key_to_set="test_app_secret", value_to_set="your_app_secret_here")
        set_key(dotenv_path=dep, key_to_set="test_database_url", value_to_set="your_database_url_here")


    @classmethod
    def tearDownClass(self):
        dep = self.get_path_of_dot_env(self)
        connect_with = dotenv_values(dep)
        if 'test_app_key' in connect_with:
            unset_key(dotenv_path=dep, key_to_unset="test_app_key")
        if 'test_app_secret' in connect_with:
            unset_key(dotenv_path=dep, key_to_unset="test_app_secret")
        if 'test_database_url' in connect_with:
            unset_key(dotenv_path=dep, key_to_unset="test_database_url")

    #

    def test_gitignore_exists(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertTrue(gitignore.exists(), f".gitignore not found at {gitignore}")

    def test_gitignore_contains_env_pattern(self):
        gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
        self.assertIn("*.env", gitignore.read_text(), ".gitignore does not contain '*.env'")

    def test_sqlite_running(self):
        conn = sqlite3.connect(':memory:')  # Connect to an in-memory database
        self.assertIsNotNone(conn, "expecting sqlite3 daemon")
        conn.close()  # Close the connection

    def test_read_from_dotenv(self):
        dot_env_path = self.get_path_of_dot_env()
        connect_with = dotenv_values(dot_env_path)
        # confirm variables can be read from .env
        key_ok = connect_with['test_app_key'] == "your_app_key_here"
        secret_ok = connect_with['test_app_secret'] == "your_app_secret_here"
        msg = "Expecting key and secret to be okay"
        self.assertTrue(key_ok and secret_ok, msg)



#

if __name__ == "__main__":
    test_order = ["test_gitignore_exists",
                  "test_gitignore_contains_env_pattern",
                  "test_sqlite_running"]
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUser = \
            lambda x, y: test_order.index(x) - test_order.index(y)
    unittest.main(testLoader=test_loader)

