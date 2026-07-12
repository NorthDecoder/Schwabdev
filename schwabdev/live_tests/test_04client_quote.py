import datetime
import codecs
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from dotenv import set_key
from getpass import getpass # get password w/o echo
from pathlib import Path    # manage paths
import re
import unittest

# software under test (sut)
import schwabdev

class TestClientMethods(unittest.TestCase):

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

    def decrypt_data(key, encrypted_data):
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


        # Encode a key from the user supplied passphrase
        self.key = codecs.encode(bytes(pass_phrase+pass_phrase,'utf-8'),'base64')

        # Expecting the .env file already has the encrypted app_key and app_secret
        # from a previous step in the test sequence

        connect_with = dotenv_values(self.dep)

        appkey_encrypted = connect_with['app_key']
        appsecret_encrypted = connect_with['app_secret']

        #decrypt
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
            print("\nError:\n",e)
            print(" Expecting a valid appkey and appsecret")
            print(" Exiting early, cannot proceed, invalid appkey OR appsecret")


        # Get a list of methods using dir()
        self.methods_list = [method for method in dir(self.client) if
                       callable(getattr(self.client, method))
                       and not method.startswith("__")
                       and not method.startswith("_")]

        linked_accounts = self.client.linked_accounts().json()
        # get first linked account
        self.account_hash_01 = linked_accounts[0].get('hashValue')

    #

    def test_connect_client_to_api(self):
        client_obj_str = str(self.client)

        pattern = re.compile(r'schwabdev.client.Client')
        match_list = re.findall(pattern,client_obj_str)

        msg = "Expecting to be connected with a schwabdev.client.Client"
        self.assertTrue(match_list == ['schwabdev.client.Client'] , msg)



    def test_quote_returns_dict(self):
        """
        Call quote() with a plain equity symbol.
        Expect a dict back with the symbol as a top-level key.
        """
        response = self.client.quote("AAPL")
        quote_dict = response.json()

        msg = "Expecting quote() to return a dict"
        self.assertTrue(type(quote_dict) == dict, msg)

    def test_quote_symbol_is_top_level_key(self):
        """
        The Schwab API wraps the quote under the requested symbol.
        Verify the symbol appears as a key in the response.
        """
        symbol = "AAPL"
        response = self.client.quote(symbol)
        quote_dict = response.json()

        msg = f"Expecting '{symbol}' to be a key in the quote response"
        self.assertIn(symbol, quote_dict, msg)

    def test_quote_with_fields_all(self):
        """
        Call quote() with fields="all".
        Expect a successful HTTP 200 response and a non-empty dict.
        """
        response = self.client.quote("MSFT", fields="all")

        msg = "Expecting HTTP 200 when fields='all'"
        self.assertEqual(response.status_code, 200, msg)

        quote_dict = response.json()
        msg = "Expecting a non-empty dict when fields='all'"
        self.assertTrue(len(quote_dict) > 0, msg)

    def test_quote_with_fields_quote(self):
        """
        Call quote() with fields="quote".
        Verify the 'quote' sub-key is present in the response for the symbol.
        """
        symbol = "MSFT"
        response = self.client.quote(symbol, fields="quote")
        quote_dict = response.json()

        msg = f"Expecting '{symbol}' key in response when fields='quote'"
        self.assertIn(symbol, quote_dict, msg)

        inner = quote_dict[symbol]
        msg = "Expecting 'quote' sub-key when fields='quote'"
        self.assertIn("quote", inner, msg)

    def test_quote_with_fields_fundamental(self):
        """
        Call quote() with fields="fundamental".
        Verify the 'fundamental' sub-key is present in the response.
        """
        symbol = "MSFT"
        response = self.client.quote(symbol, fields="fundamental")
        quote_dict = response.json()

        msg = f"Expecting '{symbol}' key in response when fields='fundamental'"
        self.assertIn(symbol, quote_dict, msg)

        inner = quote_dict[symbol]
        msg = "Expecting 'fundamental' sub-key when fields='fundamental'"
        self.assertIn("fundamental", inner, msg)

    def test_quote_fields_defaults_to_none(self):
        """
        Call quote() without the fields argument.
        Should behave identically to fields=None — no 400/422 error.
        Schwab returns both 'quote' and 'fundamental' by default.
        """
        response_default = self.client.quote("AAPL")
        response_none    = self.client.quote("AAPL", fields=None)

        msg = "Default call should return HTTP 200"
        self.assertEqual(response_default.status_code, 200, msg)

        msg = "Explicit fields=None should return HTTP 200"
        self.assertEqual(response_none.status_code, 200, msg)

    def test_quote_url_encodes_option_symbol(self):
        """
        Option ticker symbols contain spaces and slashes that must be
        percent-encoded before being placed in the URL path.
        urllib.parse.quote(..., safe="") handles this.  Verify the API
        accepts such a symbol without raising a client-side exception and
        returns a parseable JSON body (even if the symbol is not found,
        the response should be JSON, not a crash).
        """
        # Standard OCC option symbol format: underlying + expiry + C/P + strike
        # Schwab may use a space-separated variant:  "AAPL  250117C00150000"
        option_symbol = "AAPL  250117C00150000"

        try:
            response = self.client.quote(option_symbol)
            # Should not raise; 200 or 404 are both acceptable — we just
            # want to confirm the URL was built and sent without error.
            self.assertIn(response.status_code, [200, 400, 404],
                          "Unexpected HTTP status for option symbol quote")
        except Exception as e:
            self.fail(f"quote() raised an exception for an option symbol: {e}")

    def test_quote_response_has_expected_asset_main_type(self):
        """
        For a well-known equity, the assetMainType field should be EQUITY.
        """
        symbol = "AAPL"
        response = self.client.quote(symbol, fields="all")
        quote_dict = response.json()

        self.assertIn(symbol, quote_dict)
        asset_type = quote_dict[symbol].get("assetMainType")

        msg = "Expecting assetMainType to be 'EQUITY' for AAPL"
        self.assertEqual(asset_type, "EQUITY", msg)

    def test_quote_invalid_symbol_returns_error_response(self):
        """
        Passing a symbol that does not exist should return a non-200
        HTTP status (typically 400 or 404) rather than raising an exception.
        The library should not crash on a bad symbol.
        """
        response = self.client.quote("ZZZZZZZZZZZZ_INVALID")

        msg = "Expecting a non-200 status for an invalid symbol"
        self.assertNotEqual(response.status_code, 200, msg)

#

if __name__ == "__main__":
    test_order = [
        test_connect_client_to_api,
    ]
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUser = \
            lambda x, y: test_order.index(x) - test_order.index(y)
    unittest.main(testLoader=test_loader)
    unittest.main()
