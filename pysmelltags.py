# pysmelltags.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 


import sys, os
from codefinder import ModuleDict, processFile
from idehelper import findRootPackageList
from pprint import pprint

__version__ = "v0.4"

source = """
class Aclass(object):
    def do_stuff(self):
        a = 1
        print a
        self.bar = 42

    def do_other_stuff(self):
        self.bar().do_stuff()
        self.baz.do_stuff()

def test(aname):
    aname.do_stuff()
    aname.do_other_stuff()
"""


def generateClassTag(modules, output):
    p = os.path.join(os.getcwd(), output)
    f = open(p, 'w')
    pprint(modules, f, width=100)
    f.close()


def process(argList, excluded, output):
    modules = ModuleDict()
    for rootPackage in fileList:
        if os.path.isdir(rootPackage):
            for path, dirs, files in os.walk(rootPackage):
                if rootPackage == '.':
                    rootPackage = os.path.split(os.getcwd())[-1]
                if os.path.basename(path) in excluded:
                    continue
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    #path here is relative, make it absolute
                    absPath = os.path.abspath(path)
                    newmodules = processFile(f, absPath, rootPackage)
                    modules.update(newmodules)
        else: # single file
            filename = rootPackage
            rootPackageList = findRootPackageList(os.getcwd(), filename)
            absPath = os.path.abspath(".")
            #path here is absolute
            newmodules = processFile(filename, absPath, rootPackageList[0])
            modules.update(newmodules)
            
    generateClassTag(modules, output)



if __name__ == '__main__':
    fileList = sys.argv[1:]
    if not fileList:
        print """\
PySmell %s

usage: python pysmelltags.py package [package, ...] [-x excluded, ...] [options]

Generate a PYSMELLTAGS file with information about the Python code contained
in the specified packages (recursively). This file is then used to
provide autocompletion for various IDEs and editors that support it.

Options:

    -x args   Will not analyze files in directories that match the argument.
              Useful for excluding tests or version control directories.

    -o FILE   Will redirect the output to FILE instead of PYSMELLTAGS

    -t        Will print timing information.
""" % __version__
        sys.exit(0)
    timing = False
    output = 'PYSMELLTAGS'
    excluded = []
    if '-t' in fileList:
        timing = True
        fileList.remove('-t')

    if '-o' in fileList:
        fileList.remove('-o')
        output = fileList.pop()

    if '-x' in fileList:
        excluded = fileList[fileList.index('-x')+1:]
        fileList = fileList[:fileList.index('-x')]
    if not fileList:
        fileList = [os.getcwd()]

    if timing:
        import time
        start = time.clock()
    process(fileList, excluded, output)
    if timing:
        took = time.clock() - start
        print 'took %f seconds' % took


