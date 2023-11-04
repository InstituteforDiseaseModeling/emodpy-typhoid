# emodpy-typhoid tests

## How to run these tests after you have emodpy-typhoid installed in a virtual environment.

### prerequisites:
Active your virtual environment

Install pytest: `pip install pytest`

Install idm-test: `pip install idm-test --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple`

Login to comps2: `python .dev_scripts/create_auth_token_args.py -u youremail@idmod.org -p password`

### Run unit tests:
`cd tests/unitests`

`py.test -sv --junitxml=reports/test_results.xml`

### Run integration tests:
`cd tests/workflow_tests`

`py.test -sv --junitxml=reports/test_results.xml`

### Run sft tests:
`cd tests\sft_tests`

`python run_all_sft_tests.py`