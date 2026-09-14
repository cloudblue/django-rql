#
#  Copyright © 2026 CloudBlue. All rights reserved.
#

from py_rql.exceptions import RQLFilterParsingError
from py_rql.parser import RQLParser

from dj_rql.drf._utils import get_query
from dj_rql.drf.backend import RQLFilterBackend
from dj_rql.transformer import RQLSelectTransformer


def _get_query_for_request(drf_request):
    """Query of a request, resolved by its view's RQL backend when there is one.

    A backend is free to rewrite the query before filtering, as the compatibility ones
    do, so reading the query string of the request would not give what the filtering
    will end up seeing. DRF leaves the view on the request, which is what makes asking
    the backend possible without the caller passing anything.
    """
    view = (getattr(drf_request, 'parser_context', None) or {}).get('view')

    for backend in getattr(view, 'filter_backends', None) or ():
        if isinstance(backend, type) and issubclass(backend, RQLFilterBackend):
            return backend.get_query_for_view(drf_request, view)

    return get_query(drf_request)


def get_select_props(drf_request) -> tuple:
    """Props requested through the RQL `select(...)` expression of a request query.

    Reads the props straight from the query, which makes it usable from
    `get_queryset()`, before any filtering has run. Prefer it over
    `request.rql_select`, which the filter backend only sets while filtering, and
    only for filter classes with `SELECT = True`.

    Args:
        drf_request (Request): Request from API view, or `None`.

    Returns:
        tuple: Requested props, as raw signed names, e.g. `('books', '-author.email')`.

    Notes:
        Props are returned as the query wrote them: dotted paths stay whole, exclusions
        keep their `-` prefix, order and repetitions are preserved, and nothing is
        checked against the filters of any filter class. It is up to the caller to
        decide what a prop means to it, keeping in mind that a prop selects everything
        below it, so `select(author.email)` selects `author` as well.

        Props of every select operation are returned, even though a query is allowed to
        hold only one. Rejecting such a query stays the job of
        `RQLFilterClass.apply_filters`, which runs later, together with rejecting a
        query that cannot be parsed: that one yields no props here rather than raising,
        so that this is never the reason a request fails before the filtering has had
        its say.

        Nothing is memoised, so keep the returned tuple around instead of calling this
        once per prop.
    """
    if drf_request is None:
        return ()

    rql_ast = getattr(drf_request, 'rql_ast', None)

    if rql_ast is None:
        try:
            query = _get_query_for_request(drf_request)
            if not query:
                return ()

            rql_ast = RQLParser.parse_query(query)
        except RQLFilterParsingError:
            return ()

    return RQLSelectTransformer().transform(rql_ast)
