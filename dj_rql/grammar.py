# flake8: noqa

from __future__ import unicode_literals


RQL_GRAMMAR = r"""
start: term?

term: expr_term
    | logical
    
expr_term: comp
    
logical: and_op
    | or_op
    | not_op
    
and_op: _and 
    | _L_BRACE _and _R_BRACE

_and: _AND _logical_exp
    | term "&" term
    | term _COMA term

or_op: _L_BRACE _or _R_BRACE

_or: _OR _logical_exp
    | term "|" term
    | term ";" term

_logical_exp: _L_BRACE expr_term (_COMA expr_term)+ _R_BRACE

not_op: _NOT _L_BRACE expr_term _R_BRACE

comp: comp_term _L_BRACE prop _COMA val _R_BRACE
    | prop _EQUALITY comp_term _EQUALITY val
    | prop _EQUALITY val
    
val: prop
    | QUOTED_VAL
    | UNQUOTED_VAL
    
prop: comp_term
    | logical_term
    | PROP
    
!comp_term: "eq" | "ne" | "gt" | "ge" | "lt" | "le"
!logical_term: _AND | _OR | _NOT

    
PROP: /[a-zA-Z]/ /[\w\-\.]/*
QUOTED_VAL: /"[^"]*"/
    | /'[^']*'/
UNQUOTED_VAL: /[\w\-]/ /[\w\.\-\:\+]/*

_AND: "and"
_OR: "or"
_NOT: "not"

_COMA: ","
_L_BRACE: "("
_R_BRACE: ")"
_EQUALITY: "="
"""
