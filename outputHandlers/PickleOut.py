#!/usr/bin/env python
# pysmell.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved

import cPickle as pickle
import os

version = __import__('pysmell').__version__

class PickleOut():
    def __init__(self, filePath):
        self.filePath = os.path.abspath(filePath)

    def write(self, modules):
        f = open(self.filePath, 'wb')
        pickle.dump(modules, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()
