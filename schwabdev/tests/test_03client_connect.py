import codecs
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from dotenv import set_key
from getpass import getpass # get password w/o echo
from pathlib import Path    # manage paths
import re
#import sqlite3
import unittest

# software under test (sut)
import schwabdev

class TestEncryption(unittest.TestCase):

    # class variables
    app_key_input = ""
    app_secret_input = ""
    key = ""

    def get_path_of_dot_env(self):
        # define where the file will be
        return Path(__file__).resolve().parents[2] / ".env"

    #

    def confirm_ignore_dot_env(self):
        """
        Make sure there is a *.env on one line in the .gitignore
        file and that the the text is at the very beginning of the
        line, ie not commented out.
        """
        git_ignore_path = Path(__file__).resolve().parents[2] / ".gitignore"
        ignored_text = git_ignore_path.read_text()
        pattern = re.compile(r'\n\*\.env')
        match_list = re.findall(pattern,ignored_text)

        if match_list == ['\n*.env']:
            result = True
        else:
            result = False

        return result

    #

    def decrypt_data(self, key, encrypted_data):
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data

    #

    @classmethod
    def setUpClass(self):
        print("\n")
        print("Attempting to connect the SchwabDev client to the API")
        print(24*"==")

        self.dep = self.get_path_of_dot_env(self)

        if self.confirm_ignore_dot_env(self) == True:
            pass # dot_env is ignored
        else:
            print("\nDANGER: There is no *.env in the .gitignore file!")
            print("Exiting early.\n")
            exit()

        if self.dep.exists():
            print("The .env file already exists, no need to create")
            pass
        else:
            msg = "\n The .env file was expected to already exist from"
            msg += "a previous test step. Redo test step 02"
            print(msg)
            print("Exiting early.\n")
            exit()
        #

        print("\n",15 * "* ~ ")
        print("Preparing to recover the encrypted key and secret from the .env file")
        print("\n",15 * "* ~ ")
        pass_phrase = ""
        while len(pass_phrase) != 16:
            print("Enter the sixteen digit passphrase previously memorized: ")
            pass_phrase = getpass()
            if len(pass_phrase) == 16:
                pass
            else:
                print("\npass_phrase length not equal to 16!\n")


        # Create Fernet key from passphrase
        self.key = codecs.encode(bytes(pass_phrase+pass_phrase,'utf-8'),'base64')
        fernet_key = Fernet(self.key)

        # Expecting the .env file already has the encrypted app_key and app_secret
        # from a previous step in the test sequence


    def test_connect_client_to_api(self):
        connect_with = dotenv_values(self.dep)

        appkey_encrypted = connect_with['app_key']
        appsecret_encrypted = connect_with['app_secret']

        #decrypt
        appkey = self.decrypt_data(self.key, appkey_encrypted)
        appsecret = self.decrypt_data(self.key, appsecret_encrypted)

        try:
            client = schwabdev.Client(appkey, appsecret)
            print("\n Test connected with client:\n", client)
            # expecing something like
            # client: <schwabdev.client.Client object at 0x7f5fd0c0b0e0>
        except Exception as e:
            print("file:", Path(__file__))
            print(" in function test_connect_client_to_api")
            print("\nError:\n",e)
            print(" Expecting a valid appkey and appsecret")
            print(" Exiting early, cannot proceed, invalid appkey OR appsecret")

        client_obj_str = str(client)

        pattern = re.compile(r'schwabdev.client.Client')
        match_list = re.findall(pattern,client_obj_str)

        msg = "Expecting to be connected with a schwabdev.client.Client"
        self.assertTrue(match_list == ['schwabdev.client.Client'] , msg)


#

if __name__ == "__main__":
    #test_order = []
    #test_loader = unittest.TestLoader()
    #test_loader.sortTestMethodsUser = \
    #        lambda x, y: test_order.index(x) - test_order.index(y)
    #unittest.main(testLoader=test_loader)
    unittest.main()
