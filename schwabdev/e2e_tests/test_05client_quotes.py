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


    # ------------------------------------------------------------------
    # quotes() coverage
    # ------------------------------------------------------------------

    def test_quotes_returns_dict(self):
        """
        Call quotes() with a list of equity symbols.
        Expect a dict back keyed by symbol.
        """
        response = self.client.quotes(["AAPL", "INTC"])
        quotes_dict = response.json()

        msg = "Expecting quotes() to return a dict"
        self.assertTrue(type(quotes_dict) == dict, msg)

    def test_quotes_accepts_list_of_symbols(self):
        """
        Passing symbols as a python list should be converted to a
        comma separated string internally and both symbols should be
        present as top-level keys in the response.
        """
        symbols = ["AAPL", "INTC"]
        response = self.client.quotes(symbols)
        quotes_dict = response.json()

        for symbol in symbols:
            msg = f"Expecting '{symbol}' to be a key in the quotes response"
            self.assertIn(symbol, quotes_dict, msg)

    def test_quotes_accepts_comma_separated_string(self):
        """
        Passing symbols as a single comma separated string should behave
        the same as passing a list.
        """
        response = self.client.quotes("AAPL,INTC")
        quotes_dict = response.json()

        for symbol in ["AAPL", "INTC"]:
            msg = f"Expecting '{symbol}' to be a key in the quotes response"
            self.assertIn(symbol, quotes_dict, msg)

    def test_quotes_single_symbol_in_list(self):
        """
        A list containing a single symbol should still work and return
        that symbol as a top-level key.
        """
        response = self.client.quotes(["MSFT"])
        quotes_dict = response.json()

        msg = "Expecting 'MSFT' to be a key in the quotes response"
        self.assertIn("MSFT", quotes_dict, msg)

    def test_quotes_with_fields_all(self):
        """
        Call quotes() with fields="all".
        Expect a successful HTTP 200 response and a non-empty dict.
        """
        response = self.client.quotes(["AAPL", "MSFT"], fields="all")

        msg = "Expecting HTTP 200 when fields='all'"
        self.assertEqual(response.status_code, 200, msg)

        quotes_dict = response.json()
        msg = "Expecting a non-empty dict when fields='all'"
        self.assertTrue(len(quotes_dict) > 0, msg)

    def test_quotes_with_fields_quote(self):
        """
        Call quotes() with fields="quote".
        Verify the 'quote' sub-key is present for each requested symbol.
        """
        symbols = ["AAPL", "MSFT"]
        response = self.client.quotes(symbols, fields="quote")
        quotes_dict = response.json()

        for symbol in symbols:
            msg = f"Expecting '{symbol}' key in response when fields='quote'"
            self.assertIn(symbol, quotes_dict, msg)

            inner = quotes_dict[symbol]
            msg = "Expecting 'quote' sub-key when fields='quote'"
            self.assertIn("quote", inner, msg)

    def test_quotes_with_fields_fundamental(self):
        """
        Call quotes() with fields="fundamental".
        Verify the 'fundamental' sub-key is present for each symbol.
        """
        symbols = ["AAPL", "MSFT"]
        response = self.client.quotes(symbols, fields="fundamental")
        quotes_dict = response.json()

        for symbol in symbols:
            msg = f"Expecting '{symbol}' key in response when fields='fundamental'"
            self.assertIn(symbol, quotes_dict, msg)

            inner = quotes_dict[symbol]
            msg = "Expecting 'fundamental' sub-key when fields='fundamental'"
            self.assertIn("fundamental", inner, msg)

    def test_quotes_fields_defaults_to_none(self):
        """
        Call quotes() without the fields argument.
        Should behave identically to fields=None — no 400/422 error.
        """
        response_default = self.client.quotes(["AAPL", "MSFT"])
        response_none    = self.client.quotes(["AAPL", "MSFT"], fields=None)

        msg = "Default call should return HTTP 200"
        self.assertEqual(response_default.status_code, 200, msg)

        msg = "Explicit fields=None should return HTTP 200"
        self.assertEqual(response_none.status_code, 200, msg)

    def test_quotes_indicative_defaults_to_false(self):
        """
        indicative defaults to False. Confirm the request still succeeds
        and behaves the same as explicitly passing indicative=False.
        """
        response_default = self.client.quotes(["AAPL", "MSFT"])
        response_explicit = self.client.quotes(["AAPL", "MSFT"], indicative=False)

        msg = "Default indicative call should return HTTP 200"
        self.assertEqual(response_default.status_code, 200, msg)

        msg = "Explicit indicative=False call should return HTTP 200"
        self.assertEqual(response_explicit.status_code, 200, msg)

    def test_quotes_indicative_true(self):
        """
        Call quotes() with indicative=True for an ETF/index-style symbol
        and confirm the call succeeds without raising.
        """
        try:
            response = self.client.quotes(["SPY"], indicative=True)
            msg = "Expecting HTTP 200 when indicative=True"
            self.assertEqual(response.status_code, 200, msg)
        except Exception as e:
            self.fail(f"quotes() raised an exception with indicative=True: {e}")

    def test_quotes_response_has_expected_asset_main_type(self):
        """
        For well-known equities, the assetMainType field should be EQUITY
        for each requested symbol.
        """
        symbols = ["AAPL", "MSFT"]
        response = self.client.quotes(symbols, fields="all")
        quotes_dict = response.json()

        for symbol in symbols:
            self.assertIn(symbol, quotes_dict)
            asset_type = quotes_dict[symbol].get("assetMainType")

            msg = f"Expecting assetMainType to be 'EQUITY' for {symbol}"
            self.assertEqual(asset_type, "EQUITY", msg)

    def test_quotes_url_encodes_option_symbols(self):
        """
        Option ticker symbols contain spaces and slashes. Verify the API
        accepts a list containing such a symbol without raising a
        client-side exception and returns a parseable JSON body (even if
        the symbol is not found, the response should be JSON, not a crash).
        """
        # Standard OCC option symbol format: underlying + expiry + C/P + strike
        option_symbol = "AAPL  250117C00150000"

        try:
            response = self.client.quotes([option_symbol, "AAPL"])
            self.assertIn(response.status_code, [200, 400, 404],
                          "Unexpected HTTP status for option symbol quotes")
        except Exception as e:
            self.fail(f"quotes() raised an exception for an option symbol: {e}")

    def test_quotes_invalid_symbol_returns_error_response(self):
        """
        Passing a symbol that does not exist may return a 200 HTTP status
        code while reporting symbol-level errors in the response body.

        The library should not crash on a bad symbol.
        """
        response = self.client.quotes(["ZZZZZZZZZZZZ_INVALID"])
        response_dict = response.json()

        #inv_S = response_dict['errors']['invalidSymbols'] == ["ZZZZZZZZZZZZ_INVALID"]
        inv_S = response_dict['errors']['invalidSymbols'] != None
        val_R = response.status_code == 200

        msg = "May receive a 200 status_code "
        msg += "and response.content errors:invalidSymbols"
        self.assertTrue(inv_S and val_R, msg)

    def test_quotes_mixed_valid_and_invalid_symbols(self):
        """
        A request containing both a valid and an invalid symbol should
        still return JSON. Schwab typically returns partial data along
        with an 'error' section rather than failing the whole request.
        """
        response = self.client.quotes(["AAPL", "ZZZZZZZZZZZZ_INVALID"])

        try:
            quotes_dict = response.json()
        except Exception as e:
            self.fail(f"quotes() response was not valid JSON: {e}")

        msg = "Expecting valid symbol 'AAPL' to still be present in mixed request"
        self.assertIn("AAPL", quotes_dict, msg)

    def test_quotes_empty_list_raises_or_errors(self):
        """
        Passing an empty list of symbols should not crash the client;
        the server is expected to respond with a non-200 status since
        no symbols were provided.
        """
        try:
            response = self.client.quotes([])
            msg = "Expecting a non-200 status for an empty symbols list"
            self.assertNotEqual(response.status_code, 200, msg)
        except Exception as e:
            self.fail(f"quotes() raised an exception for an empty symbols list: {e}")

#

if __name__ == "__main__":
    test_order = [
        "test_connect_client_to_api",
    ]
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUser = \
            lambda x, y: test_order.index(x) - test_order.index(y)
    unittest.main(testLoader=test_loader)
    unittest.main()
