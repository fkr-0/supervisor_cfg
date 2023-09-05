#!/usr/bin/env python3

from importlib.util import find_spec

try:
    find_spec("supervisor_cfg.rpcinterface")
except ImportError:
    pass
