def pytest_addoption(parser):
    parser.addoption('--requests', action='store_true', dest="requests",
                 default=False, help="enable tests with real API requests")

def pytest_configure(config):
    if not config.option.requests:
        setattr(config.option, 'markexpr', 'not requests')
