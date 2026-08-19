import datetime as dt
import codecs
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from dotenv import set_key
from getpass import getpass  # get password w/o echo
from pathlib import Path  # manage paths
import re
import unittest

# software under test (sut)
import schwabdev


class TestClientOrderMethods(unittest.TestCase):

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
        pattern = re.compile(r"\n\*\.env")
        match_list = re.findall(pattern, ignored_text)

        if match_list == ["\n*.env"]:
            result = True
        else:
            result = False

        return result

    #

    def decrypt_data(key, encrypted_data):
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data

    #

    @classmethod
    def setUpClass(self):
        print("\n")
        print("Attempting to connect the SchwabDev client to the API")
        print(24 * "==")

        self.dep = self.get_path_of_dot_env(self)

        if self.confirm_ignore_dot_env(self) == True:
            pass  # dot_env is ignored
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

        print("\n", 15 * "* ~ ")
        print("Preparing to recover the encrypted key and secret from the .env file")
        print("\n", 15 * "* ~ ")
        pass_phrase = ""
        while len(pass_phrase) != 16:
            print("Enter the sixteen digit passphrase previously memorized: ")
            pass_phrase = getpass()
            if len(pass_phrase) == 16:
                pass
            else:
                print("\npass_phrase length not equal to 16!\n")

        # Encode a key from the user supplied passphrase
        self.key = codecs.encode(bytes(pass_phrase + pass_phrase, "utf-8"), "base64")

        # Expecting the .env file already has the encrypted app_key and app_secret
        # from a previous step in the test sequence

        connect_with = dotenv_values(self.dep)

        appkey_encrypted = connect_with["app_key"]
        appsecret_encrypted = connect_with["app_secret"]

        # decrypt
        appkey = self.decrypt_data(self.key, appkey_encrypted)
        appsecret = self.decrypt_data(self.key, appsecret_encrypted)

        try:
            self.client = schwabdev.Client(appkey, appsecret)
            print("\n Test connected with client:\n", self.client)
            # expecing something like
            # client: <schwabdev.client.Client object at 0x7f5fd0c0b0e0>
        except Exception as e:
            print("file:", Path(__file__))
            print(" in function setUpClass")
            print("\nError:\n", e)
            print(" Expecting a valid appkey and appsecret")
            print(" Exiting early, cannot proceed, invalid appkey OR appsecret")

        # Get a list of methods using dir()
        self.methods_list = [
            method
            for method in dir(self.client)
            if callable(getattr(self.client, method))
            and not method.startswith("__")
            and not method.startswith("_")
        ]

        linked_accounts = self.client.linked_accounts().json()
        # get first linked account
        self.account_hash_01 = linked_accounts[0].get("hashValue")

    #

    def test_connect_client_to_api(self):
        client_obj_str = str(self.client)

        pattern = re.compile(r"schwabdev.client.Client")
        match_list = re.findall(pattern, client_obj_str)

        msg = "Expecting to be connected with a schwabdev.client.Client"
        self.assertTrue(match_list == ["schwabdev.client.Client"], msg)

    # ------------------------------------------------------------------
    # orders() coverage
    # ------------------------------------------------------------------

    # execute a possible workflow for placing a live order

    # 1. Determine session hours
    # 2. Check symbol
    #    a. preexisting similar orders
    #    b. ask price
    # 3. Preview an impossibly low priced buy order
    #

    def get_example_order(self):
        """
        An impossibly low priced example order
        """
        example_order = {}
        example_order["orderType"] = "LIMIT"
        example_order["session"] = "SEAMLESS"
        example_order["duration"] = "GOOD_TILL_CANCEL"
        example_order["orderStrategyType"] = "SINGLE"
        example_order["price"] = "00.01"  # impossibly low
        example_order["orderLegCollection"] = [{}]  # a list of order legs
        example_order["orderLegCollection"][0] = {
            "instruction": "BUY",
            "quantity": 1,
            "instrument": {
                "symbol": "SPY",
                "assetType": "EQUITY",
            },
        }
        return example_order

    def test_preview_order_returns_dict(self):
        """
        Call client.preview_order returns details in an order dictionary.
        Preview order with a bid price that is significantly lower than
        current market price.  Expect response status to be rejected.
        """
        xo = self.get_example_order()

        response = self.client.preview_order(self.account_hash_01, xo)
        preview_dict = response.json()

        msg = "Expecting response.json() to return a dict"
        self.assertTrue(type(preview_dict) == dict, msg)

        preview_status = preview_dict["orderStrategy"]["status"]
        msg = "Expecting REJECTED because"
        msg += " 'Your limit price is significantly away from the"
        msg += " current market price....'"
        self.assertTrue(preview_status == "REJECTED", msg)


#

if __name__ == "__main__":
    test_order = [
        "test_connect_client_to_api",
    ]
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUser = lambda x, y: test_order.index(
        x
    ) - test_order.index(y)
    unittest.main(testLoader=test_loader)
    unittest.main()
