# codefinder2.py
# Statically analyze python code
#
# Copyright (C) 2011 by Rohde Fischer <rohdef@rohdef.dk> www.rohdef.dk
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import os
import sys
import builtins
import ast

class ModuleDict(dict):
    def __init__(self):
        self._modules = {'CLASSES': {}, 'FUNCTIONS': [], 'CONSTANTS': [], 'POINTERS': {}, 'HIERARCHY': []}

    def enterModule(self, module):
        self.currentModule = module
        self['HIERARCHY'].append(module)

    def exitModule(self):
        self.currentModule = None

    def currentClass(self, klass):
        fullClass = "%s.%s" % (self.currentModule, klass)
        return self['CLASSES'][fullClass]

    def enterClass(self, klass, bases, docstring):
        fullClass = "%s.%s" % (self.currentModule, klass)
        self['CLASSES'][fullClass] = {}
        self['CLASSES'][fullClass]['methods'] = []
        self['CLASSES'][fullClass]['properties'] = []
        self['CLASSES'][fullClass]['constructor'] = []
        self['CLASSES'][fullClass]['bases'] = bases
        self['CLASSES'][fullClass]['docstring'] = docstring

    def addMethod(self, klass, method, args, docstring):
        if (method, args, docstring) not in self.currentClass(klass)['methods']:
            self.currentClass(klass)['methods'].append((method, args, docstring))

    def addPointer(self, name, pointer):
        self['POINTERS'][name] = pointer

    def addFunction(self, function, args, docstring):
        fullFunction = "%s.%s" % (self.currentModule, function)
        self['FUNCTIONS'].append((fullFunction, args, docstring))

    def addProperty(self, klass, prop):
        if klass is not None:
            if prop not in self.currentClass(klass)['properties']:
                self.currentClass(klass)['properties'].append(prop)
        else:
            fullProp = "%s.%s" % (self.currentModule, prop)
            self['CONSTANTS'].append(fullProp)

    def setConstructor(self, klass, args):
        fullClass = "%s.%s" % (self.currentModule, klass)
        self['CLASSES'][fullClass]['constructor'] = args

    def update(self, other):
        if other:
            self['CONSTANTS'].extend(other['CONSTANTS'])
            self['FUNCTIONS'].extend(other['FUNCTIONS'])
            self['HIERARCHY'].extend(other['HIERARCHY'])
            self['CLASSES'].update(other['CLASSES'])
            self['POINTERS'].update(other['POINTERS'])

    def keys(self):
        return list(self._modules.keys())

    def values(self):
        return list(self._modules.values())

    def items(self):
        return list(self._modules.items())

    def iteritems(self):
        return iter(self._modules.items())

    def __getitem__(self, item):
        return self._modules[item]

    def __len__(self):
        return len(list(self.keys()))

    def __eq__(self, other):
        return ((isinstance(other, ModuleDict) and other._modules == self._modules) or
               (isinstance(other, dict) and other == self._modules))
              

    def __ne__(self, other):
        return not self == other

def VisitChildren(fun):
    """
    Visit the children of the given node, ensuring that all details are registered.
    Eg. when visiting a class we also want to visit it's functions.
    """
    def decorated(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        self.generic_visit(args[0])
    return decorated

class CodeFinder2(ast.NodeVisitor):
    """
    Walk through the nodes of the python tree, to build the module dictionary.
    """
    
    def __init__(self):
        self.imports = {}
        self.scope = []
        self.modules = ModuleDict()
        self.module = '__module__'
        self.__package = '__package__'
        self.path = '__path__'
    
    def __setPackage(self, package):
        """ Ensures a dot in the end of the packagename """
        if package:
            self.__package = package + '.'
        else:
            self.__package = ''

    package = property(lambda s: s.__package, __setPackage)
    
    def enterScope(self, node):
        self.scope.append(node)

    def exitScope(self):
        self.scope.pop()
    
    def inClassFunction(self):
        return False
    
    def qualify(self, name, curModule):
        if hasattr(__builtin__, name):
            return name
        if name in self.imports:
            return self.imports[name]
        for imp in self.imports:
            if name.startswith(imp):
                actual = self.imports[imp]
                return "%s%s" % (actual, name[len(imp):])
        if curModule:
            return '%s.%s' % (curModule, name)
        else:
            return name
    
    def isRelativeImport(self, imported):
        pathToImport = os.path.join(self.path, *imported.split('.'))
        return os.path.exists(pathToImport) or os.path.exists(pathToImport + '.py')
    
    def visit_Module(self, node):
        if self.module == '__init__':
            self.modules.enterModule('%s' % self.package[:-1]) # remove dot
        else:
            self.modules.enterModule('%s%s' % (self.package, self.module))
        ast.NodeVisitor.generic_visit(self, node)
        self.modules.exitModule()
    
    @VisitChildren
    def visit_Import(self, node):
        for name in node.names:
            imported = name.name
            asName = name.asname or name.name
            
            self.imports[asName] = imported
            if self.isRelativeImport(imported):
                imported = "%s%s" % (self.package, imported)
            self.modules.addPointer("%s.%s" % (self.modules.currentModule, asName), imported)
    
    def visit_ImportFrom(self, node):
        for name in node.names:
            asName = name.asname or name.name
            imported = name.name
            
            # TODO suspicious use of node.module (there's a ? at the property in the documentation)
            if self.isRelativeImport(node.module):
                imported = "%s%s.%s" % (self.package, node.module, imported)
            else:
                imported = "%s.%s" % (node.module, imported)
            
            self.imports[asName] = imported
            self.modules.addPointer("%s.%s" % (self.modules.currentModule, asName), imported)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.modules.addProperty(None, node.id)
    
    def visit_FunctionDef(self, node):
        self.modules.addFunction(node.name, *parseFunction(node))
        
    def visit_ClassDef(self, node):
        self.enterScope(node)
        bases = [self.qualify(getValue(base), self.modules.currentModule) for base in node.bases]
        
        cv = _ClassVisitor2(node, self.modules)
        cv.generic_visit(node)
        if len(self.scope) == 1:
            self.modules.enterClass(node.name, bases, ast.get_docstring(node, True) or '')
        
        for prop in _removeDuplicates(cv.properties):
            self.modules.addProperty(node.name, prop)
        
        for method in cv.methods:
            self.modules.addMethod(node.name, method[0], *method[1])
        
        self.exitScope()

class _ClassVisitor2(ast.NodeVisitor):
    def __init__(self, klass, modules):
        self.bases = []
        self.properties = []
        self.methods = []
        self.modules = modules
        self.klass = klass
    
    def qualify(self, name, curModule):
        if hasattr(__builtin__, name):
            return name
        #if name in self.imports:
        #    return self.imports[name]
        #for imp in self.imports:
        #    if name.startswith(imp):
        #        actual = self.imports[imp]
        #        return "%s%s" % (actual, name[len(imp):])
        if curModule:
            return '%s.%s' % (curModule, name)
        else:
            return name
    
    def visit_FunctionDef(self, node):
        if node.name is not "__init__":
            # TODO related to OldDecorator test 
            self.properties.append(node.name)
            self.methods.append([node.name, parseFunction(node)])
        
        fv = _FunctionVisitor2()
        fv.generic_visit(node)
        #ast.NodeVisitor.generic_visit(self, node)
        self.properties.extend(fv.attributes)
    
    def visit_ClassDef(self, node):
        pass # Inner class, 'testNestedStuff' specifies that it should be ignored
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.properties.append(node.id)
        self.bases.append(self.qualify(node.id, self.modules.currentModule))
    
    def visit_Attribute(self, node):
        # Ignored according to testAbsoluteImports 
        pass

class _FunctionVisitor2(ast.NodeVisitor):
    def __init__(self):
        self.args = []
        self.attributes = []
        # TODO check the need for both
        self._attributes = []
        self._callArgs = []
    
    def visit_FunctionDef(self, node):
        ast.NodeVisitor.generic_visit(self, node)
    
    def visit_Call(self, node):
        for arg in node.args:
            if isinstance(arg, ast.Num):
                self._callArgs.append(str(arg.n))
        ast.NodeVisitor.generic_visit(self, node)
    
    def visit_Attribute(self, node):
        self.attributes.append(node.attr)
        self._attributes.append(node.attr)
        ast.NodeVisitor.generic_visit(self, node)
    
    def visit_Name(self, node):
        """
        Handles function parameters, and adds them to the parameter list.
        """
        # TODO this check can be done way better!
        if (node.id != "self"):
            if isinstance(node.ctx, ast.Param):
                self.args.append(node.id)
            # Append the default value to the last parameter (there better be a better way to do this)
            elif isinstance(node.ctx, ast.Load):
                attrs = ""
                callArgs = ""
                if len(self._attributes) > 0:
                    self._attributes.reverse()
                    attrs = ".%s" % ".".join(self._attributes)
                    callArgs = "(%s)" % ",".join(self._callArgs)
          #      self.args[len(self.args)-1] += "=%s%s%s" % (node.id, attrs, callArgs)
                self._attributes = []
                self._callArgs = []
            #else:
            #    print "Name found and ignored: %s of context %s" % (node.id, node.ctx)
        ast.NodeVisitor.generic_visit(self, node)

def _removeDuplicates(myList):
    seen = set()
    seen_add = seen.add
    return [ x for x in myList if x not in seen and not seen_add(x) ]

def parseFunction(node):
    """
    Parse the function using _FunctionVisitor2. Returns a tuple containing a list of args and a docstring.
    
    Returns: a tuple containing the
    """
    
    args = []
    for arg in node.args.args:
        if isinstance(arg, ast.Name):
            if arg.id != "self":
                args.append(arg.id)
        elif isinstance(arg, ast.Tuple):
            args.append(getValue(arg))
        else:
            print(arg)
    
    offset = 1
    for default in reversed(node.args.defaults):
        args[-offset] += "=%s" % getValue(default)
        offset += 1
    
    if (node.args.vararg):
        args.append("*%s" % node.args.vararg)
    if (node.args.kwarg):
        args.append("**%s" % node.args.kwarg)
    
    docstring = ast.get_docstring(node, True)
    
    return (args, docstring or "")

def getValue(node):
    """
    Tries to get a sensible value out of a node, such as getting the value of a function argument
    and similar.
    
    Example of usage:
    """
    
    if node is None: return ''
    elif isinstance(node, ast.Num):
        if isinstance(node.n, int):
            return str(node.n)+"L"
        return str(node.n)
    elif isinstance(node, ast.Str):
        return "'%s'" % node.s
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Call):
        args = []
        for arg in node.args:
            args.append(getValue(arg))
        
        for keyword in node.keywords:
            args.append(getValue(keyword))
        # ignoring node.starargs
        if node.kwargs:
            args.append("**" + node.kwargs)
        # [str(getValue(n)) for n in node.args]
        return "%s(%s)" % (getValue(node.func), ", ".join(args))
    elif isinstance(node, ast.Attribute):
        return "%s.%s" % (getValue(node.value), node.attr)
    elif isinstance(node, ast.Dict):
        pairs = ["%s: %s" % (getValue(k), getValue(v)) for k, v in zip(node.keys, node.values)]
        return "{%s}" % (", ".join(pairs))
    elif isinstance(node, ast.Tuple):
            return "("+", ".join(getValue(element) for element in node.elts)+")"
    elif isinstance(node, ast.List):
        return "["+ ", ".join(getValue(element) for element in node.elts) +"]"
    elif isinstance(node, ast.Lambda):
        return "lambda %s: %s" % (", ".join(parseArguments(node.args)), getValue(node.body))
    elif isinstance(node, ast.Subscript):
        return "%s%s" % (getValue(node.value), getValue(node.slice))
    elif isinstance(node, ast.Slice):
        step = ""
        if node.step: step = ":%s" % getValue(node.step)
        return "[%s:%s%s]" % (getValue(node.lower), getValue(node.upper), step)
    elif isinstance(node, ast.keyword):
        return "%s=%s" % (node.arg, getValue(node.value))
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.Or):
            op = 'or'
        elif isinstance(node.op, ast.And):
            op = 'and'
        else:
            raise TypeError("Boolean operator not recognized: " + node.op)
        
        return "%s %s %s" % (getValue(node.values[0]), op, getValue(node.values[1]))
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            op = 'not'
        return "%s %s" % (op, getValue(node.operand))
    elif isinstance(node, ast.Compare):
        ops = "".join(COMPARENODES[op.__class__] for op in node.ops)
        comparators = "".join(getValue(comparator) for comparator in node.comparators)

        return "%s %s %s" % (getValue(node.left), ops, comparators)
    elif isinstance(node, ast.BinOp):
      return "%s%s%s" % (getValue(node.left), OPERATORS[node.op.__class__], getValue(node.right))
    else:
        print(node)
        raise TypeError("Unhandled type: %s" % type(node).__name__)

def parseArguments(arguments):
    return [getValue(arg) for arg in arguments.args]

def getNameTwo(template, left, right, leftJ='', rightJ=''):
    return template % (leftJ.join(map(getName, left)),
                        rightJ.join(map(getName, right)))

#MATHNODES = {
#    ast.Add: '+',
#    ast.Sub: '-',
#    ast.Mul: '*',
#    ast.Power: '**',
#    ast.Div: '/',
#    ast.Mod: '%',
#}

def getNameMath(node):
    return '%s%s%s' % (getName(node.left), MATHNODES[node.__class__], getName(node.right))

COMPARENODES = {
    ast.Eq: '==',
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}

OPERATORS = {
    ast.BitOr: "|",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
# TODO what about these?
    ast.BitXor: "",
    ast.BitAnd: "",
    ast.FloorDiv: "",
}



def getName(node):
    if node is None: return ''
    if isinstance(node, (str, int, float)):
        return str(node)
    if isinstance(node, (ast.Class, ast.Name, ast.Function)):
        return node.name
    if isinstance(node, ast.Dict):
        pairs = ['%s: %s' % pair for pair in [(getName(first), getName(second))
                        for (first, second) in node.items]]
        return '{%s}' % ', '.join(pairs)
    if isinstance(node, ast.CallFunc):
        notArgs = [n for n in node.getChildNodes() if n not in node.args]
        return getNameTwo('%s(%s)', notArgs, node.args, rightJ=', ')
    if isinstance(node, ast.Const):
        try:
            float(node.value)
            return str(node.value)
        except:
            return repr(str(node.value))
    if isinstance(node, ast.LeftShift):
        return getNameTwo('%s<<%s', node.left, node.right)
    if isinstance(node, ast.RightShift):
        return getNameTwo('%s>>%s', node.left, node.right)
    if isinstance(node, (ast.Mul, ast.Add, ast.Sub, ast.Power, ast.Div, ast.Mod)):
        return getNameMath(node)
    if isinstance(node, ast.Bitor):
        return '|'.join(map(getName, node.nodes))
    if isinstance(node, ast.UnarySub):
        return '-%s' % ''.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.List):
        return '[%s]' % ', '.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Tuple):
        return '(%s)' % ', '.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Lambda):
        return 'lambda %s: %s' % (', '.join(map(getName, node.argnames)), getName(node.code))
    if isinstance(node, ast.Getattr):
        return '.'.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Compare):
        rhs = node.asList()[-1]
        return '%s %r' % (' '.join(map(getName, node.getChildren()[:-1])), rhs.value)
    if isinstance(node, ast.Slice):
        children = node.getChildren()
        slices = children[2:]
        formSlices = []
        for sl in slices:
            if sl is None:
                formSlices.append('')
            else:
                formSlices.append(getName(sl))
        sliceStr = ':'.join(formSlices)
        return '%s[%s]' % (getName(children[0]), sliceStr)
    if isinstance(node, ast.Not):
        return "not %s" % ''.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Or):
        return " or ".join(map(getName, node.nodes))
    if isinstance(node, ast.And):
        return " and ".join(map(getName, node.nodes))
    if isinstance(node, ast.Keyword):
        return "%s=%s" % (node.name, getName(node.expr))
    return repr(node)


def argToStr(arg):
    if isinstance(arg, tuple):
        if len(arg) == 1:
            return '(%s,)' % argToStr(arg[0])
        return '(%s)' % ', '.join(argToStr(elem) for elem in arg)
    return arg
            

def getClassDict(path, codeFinder=None):
    tree = compiler.parseFile(path)
    if codeFinder is None:
        codeFinder = CodeFinder()
    compiler.walk(tree, codeFinder)
    return codeFinder.modules


def findRootPackageList(directory, filename):
    "should walk up the tree until there is no __init__.py"
    isPackage = lambda path: os.path.exists(os.path.join(path, '__init__.py'))
    if not isPackage(directory):
        return []
    packages = []
    while directory and isPackage(directory):
        directory, tail = os.path.split(directory)
        if tail:
            packages.append(tail)
    packages.reverse()
    return packages


#def findPackage(path):
#    packages = findRootPackageList(path, "")
#    package = '.'.join(packages)
#    return package
#

def processFile(f, path):
    """f is the the filename, path is the relative path in the project, root is
    the topmost package"""
    codeFinder = CodeFinder()

    packages = findRootPackageList(path, "")
    package = '.'.join(packages)
    #package = findPackage(path)
    codeFinder.package = package
    codeFinder.module = f[:-3]
    codeFinder.path = path
    try:
        assert os.path.isabs(path), "path should be absolute"
        modules = getClassDict(os.path.join(path, f), codeFinder)
        return modules
    except Exception as e:
        print('-=#=- '* 10)
        print('EXCEPTION in', os.path.join(path, f))
        print(e)
        print('-=#=- '* 10)
        return None


def analyzeFile(fullPath, tree):
    if tree is None:
        return None
    codeFinder = CodeFinder2()
    tree = ast.parse(tree, "Test code")

    absPath, filename = os.path.split(fullPath)
    codeFinder.module = filename[:-3]
    codeFinder.path = absPath

    packages = findRootPackageList(absPath, "")
    package = '.'.join(packages)
    #package = findPackage(absPath)

    codeFinder.package = package
    codeFinder.visit(tree)
    return codeFinder.modules

def getNames(tree):
    if tree is None:
        return None
    #inferer = NameVisitor()
    #compiler.walk(tree, inferer)
    #names = inferer.names
    #names.update(inferer.imports)
    #return names, inferer.klasses
    return None

def getImports(tree):
    if tree is None:
        return None
    inferer = BaseVisitor()
    compiler.walk(tree, inferer)

    return inferer.imports


def getClassAndParents(tree, lineNo):
    if tree is None:
        return None, []

    # inferer.visit?
    #classRanges = inferer.classRanges
    #classRanges.sort(sortClassRanges)
    
    #for klass, parents, start, end in classRanges:
    #    if lineNo >= start:
    #        return klass, parents
    return None, []

def sortClassRanges(a, b):
    return b[2] - a[2]

