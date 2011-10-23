#!/usr/bin/env python
# pysmell.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved

import cPickle as pickle
import os
from pprint import pprint

version = __import__('pysmell').__version__

class FileOut():
    def __init__(self, filePath):
        self.filePath = os.path.abspath(filePath)

    def write(self, output):
        f = open(self.filePath, 'w')
        f.write(output)
        f.close()
