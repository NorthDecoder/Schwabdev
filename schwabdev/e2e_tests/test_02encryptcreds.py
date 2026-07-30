import codecs
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from dotenv import set_key
from getpass import getpass  # get password w/o echo
from pathlib import Path  # manage paths
import unittest


class TestEncryption(unittest.TestCase):
    """
    With a passphrase encrypt a key value then store it in the .env file.
    Retrieve the key value pair, decrypt and then compare to original
    input.
    """

    # class variables
    app_key_input = ""
    app_secret_input = ""
    key = ""

    def get_path_of_dot_env(self):
        # define where the file will be
        return Path(__file__).resolve().parents[2] / ".env"

    #

    def confirm_ignore_dot_env(self):

        git_ignore_path = Path(__file__).resolve().parents[2] / ".gitignore"
        fp = open(git_ignore_path, "r")
        if "*.env" in fp.read():
            result = True
        else:
            result = False

        fp.close()
        return result

    #

    def decrypt_data(self, key, encrypted_data):
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data

    #

    @classmethod
    def setUpClass(self):
        dep = self.get_path_of_dot_env(self)

        if self.confirm_ignore_dot_env(self) == True:
            pass  # dot_env is ignored
        else:
            print("\nDANGER: There is no .env in the .gitignore file!")
            print("Exiting early.\n")
            exit()

        if dep.exists():
            # print("The .env file already exists, no need to create")
            pass
        else:
            # create file
            dep.touch(exist_ok=False)

        #

        print("\n", 15 * "* ~ ")
        print("Preparing to enter the real key and secret, passphrase encrypted")
        print("\n", 15 * "* ~ ")
        pass_phrase = ""
        while len(pass_phrase) != 16:
            print("Enter a sixteen digit memorable passphrase: ")
            pass_phrase = getpass()
            if len(pass_phrase) == 16:
                pass
            else:
                print("\npass_phrase length not equal to 16!\n")

        #
        # Create Fernet key from passphrase
        self.key = codecs.encode(bytes(pass_phrase + pass_phrase, "utf-8"), "base64")
        fernet_key = Fernet(self.key)

        print("\nEnter the app_key (invisible)")
        self.app_key_input = getpass()
        app_key_encrypted = fernet_key.encrypt(str(self.app_key_input).encode())
        set_key(
            dotenv_path=dep,
            key_to_set="app_key",
            value_to_set=app_key_encrypted.decode(),
        )

        print("\nEnter the app_secret (invisible)")
        self.app_secret_input = getpass()
        app_secret_encrypted = fernet_key.encrypt(str(self.app_secret_input).encode())
        set_key(
            dotenv_path=dep,
            key_to_set="app_secret",
            value_to_set=app_secret_encrypted.decode(),
        )

        print("\nApp key and secrets saved in the .env file")

    #

    def test_encrypt_decrypt_key(self):
        dep = self.get_path_of_dot_env()
        connect_with = dotenv_values(dep)
        appkey_encrypted = connect_with["app_key"]
        appkey = self.decrypt_data(self.key, appkey_encrypted)
        msg = "Expecting self.app_key_input encrypted to be same as decrypted"
        self.assertTrue(self.app_key_input == appkey, msg)

    #

    def test_encrypt_decrypt_secret(self):
        dep = self.get_path_of_dot_env()
        connect_with = dotenv_values(dep)
        appsecret_encrypted = connect_with["app_secret"]
        appsecret = self.decrypt_data(self.key, appsecret_encrypted)
        msg = "Expecting self.app_secret_input encrypted to be same as decrypted"
        self.assertTrue(self.app_secret_input == appsecret, msg)


#

if __name__ == "__main__":
    unittest.main()
