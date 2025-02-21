"""
Note: this test file was heavily influenced by its dbplyr counterpart.

https://github.com/tidyverse/dbplyr/blob/master/tests/testthat/test-verb-mutate.R
"""
    
from siuba import _, mutate, select, group_by, summarize, filter
from siuba.dply.vector import row_number

import pytest
from .helpers import assert_equal_query, data_frame, backend_notimpl, backend_sql
from string import ascii_lowercase 

DATA = data_frame(a = [1,2,3], b = [9,8,7])

@pytest.fixture(scope = "module")
def dfs(backend):
    return backend.load_df(DATA)

@pytest.mark.parametrize("query, output", [
    (mutate(x = _.a + _.b), DATA.assign(x = [10, 10, 10])),
    pytest.param( mutate(x = _.a + _.b) >> summarize(ttl = _.x.sum()), data_frame(ttl = 30.0), marks = pytest.mark.skip("TODO: failing sqlite?")),
    (mutate(x = _.a + 1, y = _.b - 1), DATA.assign(x = [2,3,4], y = [8,7,6])),
    (mutate(x = _.a + 1) >> mutate(y = _.b - 1), DATA.assign(x = [2,3,4], y = [8,7,6])),
    (mutate(x = _.a + 1, y = _.x + 1), DATA.assign(x = [2,3,4], y = [3,4,5]))
    ])
def test_mutate_basic(dfs, query, output):
    assert_equal_query(dfs, query, output)

@pytest.mark.parametrize("query, output", [
    (mutate(x = 1), DATA.assign(x = 1)),
    (mutate(x = "a"), DATA.assign(x = "a")),
    (mutate(x = 1.2), DATA.assign(x = 1.2))
    ])
def test_mutate_literal(dfs, query, output):
    assert_equal_query(dfs, query, output)


def test_select_mutate_filter(dfs):
    assert_equal_query(
            dfs,
            select(_.x == _.a) >> mutate(y = _.x * 2) >> filter(_.y == 2),
            data_frame(x = 1, y = 2)
            )

@pytest.mark.skip("TODO: check most recent vars for efficient mutate (#41)")
def test_mutate_smart_nesting(dfs):
    # y and z both use x, so should create only 1 extra query
    lazy_tbl = dfs >> mutate(x = _.a + 1, y = _.x + 1, z = _.x + 1)

    query = lazy_tbl.last_op.fromclause

    assert query is lazy_tbl.ops[0]
    assert isinstance(query.fromclause, sqlalchemy.Table )


@pytest.mark.skip("TODO: does pandas backend preserve order? (#42)")
def test_mutate_reassign_column_ordering(dfs):
    assert_equal_query(
            dfs,
            mutate(c = 3, a = 1, b = 2),
            data_frame(a = 1, b = 2, c = 3)
            )


@backend_sql
@backend_notimpl("sqlite")
def test_mutate_window_funcs(backend):
    data = data_frame(x = range(1, 5), g = [1,1,2,2])
    dfs = backend.load_df(data)
    assert_equal_query(
            dfs,
            group_by(_.g) >> mutate(row_num = row_number(_).astype(float)),
            data.assign(row_num = [1.0, 2, 1, 2])
            )


@backend_notimpl("sqlite")
def test_mutate_using_agg_expr(backend):
    data = data_frame(x = range(1, 5), g = [1,1,2,2])
    dfs = backend.load_df(data)
    assert_equal_query(
            dfs,
            group_by(_.g) >> mutate(y = _.x - _.x.mean()),
            data.assign(y = [-.5, .5, -.5, .5])
            )

@backend_sql # TODO: pandas outputs a int column
@backend_notimpl("sqlite")
def test_mutate_using_cuml_agg(backend):
    data = data_frame(x = range(1, 5), g = [1,1,2,2])
    dfs = backend.load_df(data)

    # cuml window without arrange before generates warning
    with pytest.warns(None):
        assert_equal_query(
                dfs,
                group_by(_.g) >> mutate(y = _.x.cumsum()),
                data.assign(y = [1.0, 3, 3, 7])
                )

def test_mutate_overwrites_prev(backend):
    # TODO: check that query doesn't generate a CTE
    dfs = backend.load_df(data_frame(x = range(1, 5), g = [1,1,2,2]))
    assert_equal_query(
            dfs,
            mutate(x = _.x + 1) >> mutate(x = _.x + 1),
            data_frame(x = [3,4,5,6], g = [1,1,2,2])
            )



