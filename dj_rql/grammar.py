#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

# flake8: noqa
"""
RQL EBNF LALR(1) compatible grammar for standard Lark lexer.

Notes:
    - rules are lowercase. They only consist of values, other rules and terminals.
    - TERMINALS are uppercase. They only consist of values and other terminals.
"""

RQL_GRAMMAR = r"""
start: term?

term: expr_term
    | logical
    
expr_term: comp
    | listing
    | searching
    | ordering
    | select
    | _L_BRACE expr_term _R_BRACE
    
logical: and_op
    | or_op
    | not_op
    
and_op: _and 
    | _L_BRACE _and _R_BRACE

_and: _AND _logical_exp
    | term "&" term
    | term _COMMA term

or_op: _or
    | _L_BRACE _or _R_BRACE

_or: _OR _logical_exp
    | _L_BRACE term "|" term _R_BRACE
    | _L_BRACE term ";" term _R_BRACE

_logical_exp: _L_BRACE expr_term (_COMMA expr_term)+ _R_BRACE

not_op: _NOT _L_BRACE expr_term _R_BRACE

comp: comp_term _L_BRACE prop _COMMA val _R_BRACE
    | prop _EQUALITY comp_term _EQUALITY val
    | prop _EQUALITY val
    
listing: list_term _L_BRACE prop _COMMA _L_BRACE val (_COMMA val)* _R_BRACE _R_BRACE
searching: search_term _L_BRACE prop _COMMA val _R_BRACE

ordering: ordering_term _signed_props
select: select_term _signed_props
_signed_props: _L_BRACE _R_BRACE
    | _L_BRACE sign_prop (_COMMA sign_prop)* _R_BRACE
    
val: prop
    | QUOTED_VAL
    | UNQUOTED_VAL
    
prop: comp_term
    | logical_term
    | list_term
    | search_term
    | ordering_term
    | select_term
    | PROP
    
!sign_prop: ["+"|"-"] prop
    
!comp_term: "eq" | "ne" | "gt" | "ge" | "lt" | "le"
!logical_term: _AND | _OR | _NOT
!list_term: "in" | "out"
!search_term: "like" | "ilike"
!ordering_term: "ordering"
!select_term: "select"

    
PROP: /[a-zA-Z]/ /[\w\-\.]/*
QUOTED_VAL: /"[^"]*"/
    | /'[^']*'/
UNQUOTED_VAL: NULL
    | EMPTY
    | /[\w\-\*\+\\]/ /[\w\.\s\-\:\+\@\*\\]/*

EMPTY: "empty()"
NULL: "null()"

_AND: "and"
_OR: "or"
_NOT: "not"

_COMMA: ","
_L_BRACE: "("
_R_BRACE: ")"
_EQUALITY: "="
"""
