import pytest
from .helpers import assert_equal_query, Backend, SqlBackend, data_frame

def pytest_addoption(parser):
    parser.addoption(
            "--dbs", action="store", default="sqlite", help="databases tested against (comma separated)"
            )

params_backend = [
    pytest.param(lambda: SqlBackend("postgresql"), id = "postgresql", marks=pytest.mark.postgresql),
    pytest.param(lambda: SqlBackend("sqlite"), id = "sqlite", marks=pytest.mark.sqlite),
    pytest.param(lambda: Backend("pandas"), id = "pandas", marks=pytest.mark.pandas)
    ]

@pytest.fixture(params = params_backend, scope = "session")
def backend(request):
    return request.param()

@pytest.fixture(autouse=True)
def skip_backend(request, backend):
    if request.node.get_closest_marker('skip_backend'):
        mark_args = request.node.get_closest_marker('skip_backend').args
        if backend.name in mark_args:
            pytest.skip('skipped on backend: {}'.format(backend.name)) 

