#!/usr/bin/env python
# pysmell.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved

version = __import__('pysmell').__version__

class PrintOut():
    def __init__(self):
        pass

    def write(self, output):
        print output
