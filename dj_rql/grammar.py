# flake8: noqa

from __future__ import unicode_literals


RQL_GRAMMAR = r"""
start: term?

term: comp

comp: comp_op "(" prop "," val ")"
    | prop "=" comp_op "=" val
    | prop "=" val
    
val: prop
    | QUOTED_VAL
    | UNQUOTED_VAL
    
prop: comp_op
    | PROP
    
!comp_op: "eq" | "ne" | "gt" | "ge" | "lt" | "le"
    
PROP: /[a-zA-Z]/ /[a-zA-Z\d\.\-_]/*
QUOTED_VAL: /"[^"]*"/ 
UNQUOTED_VAL: /[\w\d\-]/ /[\w\d\.\-_:+]/*
"""
