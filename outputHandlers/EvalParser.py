
from pprint import pformat

version = __import__('pysmell').__version__

class EvalParser():
    def __init__(self, outputStream):
        self.outputStream = outputStream

    def write(self, modules):
        parsedContent = pformat(modules, width=100)
        self.outputStream.write(parsedContent)
