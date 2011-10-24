#!/usr/bin/env python

# Copyright 2011 Rohde Fischer (rohdef@rohdef.dk). All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, this list of
#       conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright notice, this list
#       of conditions and the following disclaimer in the documentation and/or other materials
#       provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY ROHDE FISCHER ''AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ROHDE FISCHER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those of the
# authors and should not be interpreted as representing official policies, either expressed
# or implied, of Rohde Fischer.


# Import parsers and output streams
from pysmell.outputHandlers.FileOut import FileOut
from pysmell.outputHandlers.PrintOut import PrintOut

from pysmell.outputHandlers.PickleOut import PickleOut

from pysmell.outputHandlers.EvalParser import EvalParser

# Import the code analyser
from pysmell.tags import process

def main():
    """
    Simple demonstration program to show different usages. Comment and uncomment parsers 
    and output streams to try out different combinations. The system is made by using the 
    decorator pattern, so apart from PickleOut, any parser sould be combineable with any 
    output. If you want you should even be able to make decorators to your parsers.
    """

    # List of files to parse
    fileList = ['runPySmell.py']

    # Set the output to use
    outputStream = PrintOut()
    #outputStream = FileOut('somefile')
    
    # Set the parser
    parser = EvalParser(outputStream)
    #parser = PickleOut('somefile') # Be aware, currently pickle out serves as both parser and output stream

    # Get the modules
    modules = process(fileList)

    # Run the task :)
    parser.write(modules)


if __name__ == '__main__':
    main()
