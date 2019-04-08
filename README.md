Django RQL
==========

`django-rql` is an Django application, that implements RQL filter backend for your web application.


RQL
---

RQL (Resource query language) is designed for modern application development. It is built for the web, ready for NoSQL, and highly extensible with simple syntax. 
This is a query language fast and convenient database interaction. RQL was designed for use in URLs to request object-style data structures.


[RQL for Web](https://www.sitepen.com/blog/resource-query-language-a-query-language-for-the-web-nosql/)
[RQL Reference](https://docs.cloudblue.com/oa/8.0/sdk/api/rest/rql/index.html)

Notes
-----

Parsing is done with [Lark](https://github.com/lark-parser/lark).
The current parsing algorithm is [LALR(1)](https://www.wikiwand.com/en/LALR_parser) with standard lexer.

Development
===========

0. Python 2.7+
0. Install dependencies `requirements/dev.txt`

Testing
=======

0. Python 2.7+
0. Install dependencies `requirements/test.txt`

Check code style: `flake8`
Run tests: `pytest`

Tests reports are generated in `tests/reports`. 
* `out.xml` - JUnit test results
* `coverage.xml` - Coverage xml results

To generate HTML coverage reports use:
`--cov-report html:tests/reports/cov_html`
