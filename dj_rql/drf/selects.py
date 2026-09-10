#
#  Copyright © 2026 CloudBlue. All rights reserved.
#

from lark.exceptions import LarkError
from py_rql.exceptions import RQLFilterError
from py_rql.parser import RQLParser

from dj_rql.drf._utils import get_query
from dj_rql.transformer import RQLSelectTransformer


def get_select_props(drf_request) -> tuple:
    """Props requested through the RQL `select(...)` expression of a request query.

    Reads the props straight from the query, which makes it usable from
    `get_queryset()`, before any filtering has run. Prefer it over
    `request.rql_select`, which the filter backend only sets while filtering, and
    only for filter classes with `SELECT = True`.

    Args:
        drf_request (Request): Request from API view.

    Returns:
        tuple: Requested props, as raw signed names, e.g. `('books', '-author')`.

    Notes:
        Props are returned as the query wrote them: exclusions keep their `-` prefix,
        order and repetitions are preserved, and nothing is checked against the filters
        of any filter class. It is up to the caller to decide what a prop means to it.

        Props of every select operation are returned, even though a query is allowed to
        hold only one; and a query that cannot be parsed returns no props at all,
        instead of raising. Rejecting either of those stays the job of
        `RQLFilterClass.apply_filters`, which runs later, so that this never becomes the
        reason a request fails before it.
    """
    try:
        rql_ast = getattr(drf_request, 'rql_ast', None)

        if rql_ast is None:
            query = get_query(drf_request)
            if not query:
                return ()

            rql_ast = RQLParser.parse_query(query)

        return RQLSelectTransformer().transform(rql_ast)
    except (LarkError, RQLFilterError):
        return ()
