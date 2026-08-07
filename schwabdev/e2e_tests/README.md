# End to End testing code from the Develop branch

Test code coverage and Schwab API connectivity

The second test requests a valid Schwab credential which is
encrypted and stored in the .env file.

## Install test prerequisite packages

`pip install -e .[test]`

## Run a specific test file

```bash
python -m unittest test_01prerequisites.py
python -m unittest test_02encryptcreds.py
python -m unittest test_03client_connect.py
python -m unittest test_04client_quote.py
python -m unittest test_05client_quotes.py
python -m unittest test_06client_account.py
```

## Search for and run all the tests

The test files are named with a sequence number indicating the order that
the tests should be run. It appears that the discover feature respects
the sequence numbers.

```bash
cd ~/Schwabdev
python -m unittest discover -vv
```

## Code coverage reports

### For a test


```bash
coverage run -m unittest schwabdev/tests/test_01prerequisites.py

coverage report -m
```

### For all the tests

```bash
coverage run -m unittest discover -vv

coverage report -m
```

