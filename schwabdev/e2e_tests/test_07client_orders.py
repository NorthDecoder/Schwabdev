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

    def test_system_timezone_is_eastern(self):
        '''
        Regardless of where the server is physically located
        confirm that server time is set to Eastern Time Zone
        to match the New York Stock Exchange trading hours.
        '''

        local_now = dt.datetime.now().astimezone()
        server_timezone = local_now.tzinfo.tzname(local_now)

        msg = "Expecting server to be set to Eastern Time Zone"
        msg += " with `sudo timedatectl set-timezone America/New_York`."
        msg += f" Current setting is {server_timezone}"
        self.assertTrue(server_timezone == "EDT" or server_timezone == "EST", msg)

    def test_market_hour_returns_dict(self):
        '''
        Call client.market_hour, result must be a dictionary
        defining session hours.  Presumably it would be
        desirable to know what the market session is before
        placing a trade.
        '''

        equity_market_hours = self.client.market_hour("equity").json()
        msg = "Expecting equity_market_hours type to be dict"
        self.assertTrue(type(equity_market_hours) == dict, msg)


        for item in ["postMarket", "preMarket", "regularMarket"]:
            msg = "Expecting keys postMarket, preMarket, regularMarket"
            msg += " in equity_market_hours dictionary"
            sh = equity_market_hours["equity"]["EQ"]["sessionHours"]
            self.assertIn(item, sh, msg)

    def test_market_hour_valid_iso8601_format(self):
        '''
        Call client.market_hour, result is a dictionary
        defining session hours in ISO8601 format.  For
        brevity only check regular market start.
        '''

        def valid_iso8601_format(dt_obj):
            '''
            Input: dt_obj - datetime object in ISO8601 format
            Output: True if valid ISO8601, otherwise False
            '''
            dt_str = str(dt_obj)
            try:
                dt.datetime.fromisoformat(dt_str)
            except:
                return False
            return True

        equity_market_hours = self.client.market_hour("equity").json()

        sh = equity_market_hours["equity"]["EQ"]["sessionHours"]
        regular_market = sh["regularMarket"][0]

        msg = "Expecting equity_market_hours regularMarket start"
        msg += " to be in ISO8601 format"
        rms = dt.datetime.fromisoformat(regular_market["start"])
        is_iso = valid_iso8601_format(rms)
        self.assertTrue(is_iso, msg)


    def test_preview_order_returns_dict(self):
        '''
        Call client.preview_order returns details in an order dictionary.
        Preview order with a bid price that is significantly lower than
        current market price.  Expect response status to be rejected.
        '''
        example_order = {}
        example_order["orderType"] = "LIMIT"
        example_order["session"] = "SEAMLESS"
        example_order["duration"] = "GOOD_TILL_CANCEL"
        example_order["orderStrategyType"] = "SINGLE"
        example_order["price"] = "00.01"  # impossibly low
        example_order["orderLegCollection"] = [{}] # a list of order legs
        example_order["orderLegCollection"][0] = {
            "instruction": "BUY",
            "quantity": 1,
            "instrument": {
                "symbol": "SPY",
                "assetType": "EQUITY",
            },
        }

        response = self.client.preview_order(self.account_hash_01, example_order)
        preview_dict = response.json()
        msg = "Expecting response.json() to return a dict"
        self.assertTrue(type(preview_dict)==dict, msg)

        preview_status = preview_dict["orderStrategy"]["status"]
        msg = "Expecting REJECTED because"
        msg += " 'Your limit price is significantly away from the"
        msg += " current market price....'"
        self.assertTrue(preview_status=="REJECTED", msg)

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
