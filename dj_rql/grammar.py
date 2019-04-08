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
    | _L_COLON _and _R_COLON

_and: _AND _logical_exp
    | term "&" term
    | term _COMA term

or_op: _L_COLON _or _R_COLON

_or: _OR _logical_exp
    | term "|" term
    | term ";" term

_logical_exp: _L_COLON expr_term (_COMA expr_term)+ _R_COLON

not_op: _NOT _L_COLON expr_term _R_COLON

comp: comp_op _L_COLON prop _COMA val _R_COLON
    | prop _EQUALITY comp_op _EQUALITY val
    | prop _EQUALITY val
    
val: prop
    | QUOTED_VAL
    | UNQUOTED_VAL
    
prop: comp_op
    | res_logic
    | PROP
    
!comp_op: "eq" | "ne" | "gt" | "ge" | "lt" | "le"
!res_logic: _AND | _OR | _NOT

    
PROP: /[a-zA-Z]/ /[\w\-\.]/*
QUOTED_VAL: /"[^"]*"/
    | /'[^']*'/
UNQUOTED_VAL: /[\w\-]/ /[\w\.\-\:\+]/*

_AND: "and"
_OR: "or"
_NOT: "not"

_COMA: ","
_L_COLON: "("
_R_COLON: ")"
_EQUALITY: "="
"""
