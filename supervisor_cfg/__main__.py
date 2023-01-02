#!/usr/bin/env python3

try:
    from .rpcinterface import *
except ImportError:
    from rpcinterface import *
