import unittest
from textwrap import dedent
from codefinder import CodeFinder, infer, ModuleDict, findPackage
import compiler
from compiler.visitor import ExampleASTVisitor
from pprint import pformat

class ModuleDictTest(unittest.TestCase):
    def testUpdate(self):
        total = ModuleDict()
        total.enterModule('mod1')
        total.enterClass('cls1', [], 'doc1')
        total.enterModule('mod2')
        total.enterClass('cls2', [], 'doc2')

        self.assertEquals(pformat(total), pformat(total._modules))

        md1 = ModuleDict()
        md1.enterModule('mod1')
        md1.enterClass('cls1', [], 'doc1')

        md2 = ModuleDict()
        md2.enterModule('mod2')
        md2.enterClass('cls2', [], 'doc2')

        md3 = ModuleDict()
        md3.update(md1)
        self.assertEquals(pformat(md3), pformat(md1))
        md3.update(md2)
        self.assertEquals(pformat(md3), pformat(total))
        md3.update(None)
        self.assertEquals(pformat(md3), pformat(total))

    def testAddPointer(self):
        md = ModuleDict()
        md.addPointer('something', 'other')
        self.assertEquals(md['POINTERS'], {'something': 'other'})


class CodeFinderTest(unittest.TestCase):

    def getModule(self, source):
        tree = compiler.parse(dedent(source))
        codeFinder = CodeFinder()
        codeFinder.module = 'TestModule'
        codeFinder.package = 'TestPackage'
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        try:
            return eval(pformat(codeFinder.modules))
        except:
            print 'EXCEPTION WHEN EVALING:'
            print pformat(codeFinder.modules)
            print '=-' * 20
            raise


    def testOnlyPackage(self):
        source = """
        class A(object):
            pass
        """
        tree = compiler.parse(dedent(source))
        codeFinder = CodeFinder()
        codeFinder.package = 'TestPackage'
        codeFinder.module = '__init__'
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        expected = {'CLASSES': {'TestPackage.A': dict(docstring='', bases=['object'], constructor=[], methods=[], properties=[])},
            'FUNCTIONS': [], 'CONSTANTS': [], 'POINTERS': {}, 'HIERARCHY': ['TestPackage']}
        actual = eval(pformat(codeFinder.modules))
        self.assertEquals(actual, expected)


    def assertClasses(self, moduleDict, expected):
        self.assertEquals(moduleDict['CLASSES'], expected)


    def testSimpleClass(self):
        out = self.getModule("""
        class A(object):
            pass
        """)
        expected = {'TestPackage.TestModule.A': dict(bases=['object'], properties=[], methods=[], constructor=[], docstring='')}
        self.assertClasses(out, expected)


    def testClassParent(self):
        out = self.getModule("""
        class Parent(list):
            pass
        class A(Parent):
            pass
        """)
        expected = {'TestPackage.TestModule.A': dict(bases=['TestPackage.TestModule.Parent'], properties=[], methods=[], constructor=[], docstring=''), 'TestPackage.TestModule.Parent': dict(bases=['list'], properties=[], methods=[], constructor=[], docstring='')}
        self.assertClasses(out, expected)


    def testAdvancedDefaultArguments(self):
        out = self.getModule("""
        def function(a=1, b=2, c=None, d=4, e='string', f=Name, g={}):
            pass
        """)
        expected = ('TestPackage.TestModule.function', ['a=1', 'b=2', 'c=None', 'd=4', "e='string'", 'f=Name', 'g={}'], '')
        self.assertEquals(out['FUNCTIONS'], [expected])


    def testOldStyleDecoratorProperties(self):
        out = self.getModule("""
        class A:
            def __a(self):
                pass
            a = property(__a)
        """)
        expected = {'TestPackage.TestModule.A': dict(bases=[], properties=['a'], methods=[('__a', [], '')], constructor=[], docstring='')}
        self.assertClasses(out, expected)


    def assertNamesIsHandled(self, name):
        out = self.getModule("""
        def f(a=%s):
            pass
        """ % name)
        self.assertEquals(out['FUNCTIONS'], [('TestPackage.TestModule.f', ['a=%s' % name], '')])


    def testNames(self):
        self.assertNamesIsHandled('A.B.C(1)')
        self.assertNamesIsHandled('A.B.C()')
        self.assertNamesIsHandled('A.B.C')
        self.assertNamesIsHandled('{a: b, c: d}')
        self.assertNamesIsHandled('(a, b, c)')
        self.assertNamesIsHandled('[a, b, c]')
        self.assertNamesIsHandled('lambda a: (c, b)')
        self.assertNamesIsHandled("lambda name: name[:1] != '_'")
        self.assertNamesIsHandled("-180")
        self.assertNamesIsHandled("10*180")
        self.assertNamesIsHandled("10>>180")
        self.assertNamesIsHandled("10<<180")
        

    def testClassProperties(self):
        out = self.getModule("""
        class A(object):
            classprop = 1
            def __init__(self):
                self.plainprop = 2
                self.plainprop = 3
            @property
            def methodProp(self):
                pass
        """)
        expectedProps = ['classprop', 'plainprop', 'methodProp']
        self.assertEquals(out['CLASSES']['TestPackage.TestModule.A']['properties'], expectedProps)


    def testClassMethods(self):
        out = self.getModule("""
        class A(object):
            def method(self):
                'random docstring'
                pass
            def methodArgs(self, arg1, arg2):
                pass
            def methodTuple(self, (x, y)):
                pass
            def methodDefaultArgs(self, arg1, arg2=None):
                pass
            def methodStar(self, arg1, *args):
                pass
            def methodKW(self, arg1, **kwargs):
                pass
            def methodAll(self, arg1, *args, **kwargs):
                pass
            def methodReallyAll(self, arg1, arg2='a string', *args, **kwargs):
                pass
        """)
        expectedMethods = [('method', [], 'random docstring'),
                           ('methodArgs', ['arg1', 'arg2'], ''),
                           ('methodTuple', ['(x, y)'], ''),
                           ('methodDefaultArgs', ['arg1', 'arg2=None'], ''),
                           ('methodStar', ['arg1', '*args'], ''),
                           ('methodKW', ['arg1', '**kwargs'], ''),
                           ('methodAll', ['arg1', '*args', '**kwargs'], ''),
                           ('methodReallyAll', ['arg1', "arg2='a string'", '*args', '**kwargs'], ''),
                           ]
        self.assertEquals(out['CLASSES']['TestPackage.TestModule.A']['methods'], expectedMethods)


    def testTopLevelFunctions(self):
        out = self.getModule("""
        def TopFunction1(arg1, arg2=True, **spinach):
            'random docstring'
        def TopFunction2(arg1, arg2=False):
            'random docstring2'
        """)
        expectedFunctions = [('TestPackage.TestModule.TopFunction1', ['arg1', 'arg2=True', '**spinach'], 'random docstring'),
                             ('TestPackage.TestModule.TopFunction2', ['arg1', 'arg2=False'], 'random docstring2')]
        self.assertEquals(out['FUNCTIONS'], expectedFunctions)


    def testNestedStuff(self):
        out = self.getModule("""
        class A(object):
            def level1(self):
                class Level2(object):
                    pass
                def level2():
                    pass
                pass
            class InnerClass(object):
                def innerMethod(self):
                    pass
        """)
        self.assertEquals(len(out['CLASSES'].keys()), 1, 'should not count inner classes')
        self.assertEquals(out['CLASSES']['TestPackage.TestModule.A']['methods'], [('level1', [], '')])
        self.assertEquals(out['FUNCTIONS'], [])


    def testModuleConstants(self):
        out = self.getModule("""
        CONSTANT = 1
        """)
        self.assertEquals(out['CONSTANTS'], ['TestPackage.TestModule.CONSTANT'])


    def testArgToStr(self):
        from codefinder import argToStr
        self.assertEquals(argToStr('stuff'), 'stuff')
        self.assertEquals(argToStr(('ala', 'ma', 'kota')), '(ala, ma, kota)')
        self.assertEquals(argToStr((('x1', 'y1'), ('x2', 'y2'))), '((x1, y1), (x2, y2))')
        self.assertEquals(argToStr(('ala',)), '(ala,)')


    def testTrickyBases(self):
        "understand imports and generate the correct bases"
        out = self.getModule("""
            from TestPackage.AnotherModule import AnotherClass as Nyer
            from TestPackage.AnotherModule import AClass
            class A(Nyer, AClass):
                pass
        """)
        self.assertEquals(out['CLASSES']['TestPackage.TestModule.A'],
                        dict(constructor=[], methods=[], properties=[], docstring='',
                        bases=['TestPackage.AnotherModule.AnotherClass', 'TestPackage.AnotherModule.AClass'])
        )

    def testAbsoluteImports(self):
        "understand imports and generate the correct bases"
        out = self.getModule("""
            import TestPackage.AnotherModule
            import TestPackage as Hmer
            class A(TestPackage.AnotherModule.AClass, Hmer.AnotherModule.AnotherClass):
                pass
        """)
        self.assertEquals(out['CLASSES']['TestPackage.TestModule.A'],
                        dict(constructor=[], methods=[], properties=[], docstring='',
                        bases=['TestPackage.AnotherModule.AClass', 'TestPackage.AnotherModule.AnotherClass'])
        )

    def testImportedNames(self):
        out = self.getModule("""
            from somewhere.something import other as mother
            import somewhere.something as thing
        """)
        self.assertEquals(out['POINTERS'],
            {
                'TestPackage.TestModule.mother': 'somewhere.something.other',
                'TestPackage.TestModule.thing': 'somewhere.something',
            }
        )

    
    def testRelativeImports(self):
        import codefinder
        oldExists = codefinder.os.path.exists
        # monkeypatch relative.py into the path somewhere
        codefinder.os.path.exists = lambda _: True
        try:
            out = self.getModule("""
                import relative    
            """)
            self.assertEquals(out['POINTERS'],
                {
                    'TestPackage.TestModule.relative': 'TestPackage.relative'
                }
            )
        finally:
            codefinder.os.path.exists = oldExists


    def testHierarchy(self):
        class MockNode(object):
            node = 1
        node = MockNode()
        codeFinder = CodeFinder()
        codeFinder.visit = lambda _: None

        codeFinder.package = 'TestPackage'
        codeFinder.module = '__init__'
        codeFinder.visitModule(node)

        codeFinder.module = 'Modulo'
        codeFinder.visitModule(node)

        codeFinder.package = 'TestPackage.Another'
        codeFinder.module = '__init__'
        codeFinder.visitModule(node)

        codeFinder.module = 'Moduli'
        codeFinder.visitModule(node)

        expected = [
            'TestPackage',
            'TestPackage.Modulo',
            'TestPackage.Another',
            'TestPackage.Another.Moduli',
        ]
        self.assertEquals(codeFinder.modules['HIERARCHY'], expected)
        

        

class InferencingTest(unittest.TestCase):
    def testInferSelfSimple(self):
        source = dedent("""\
            import something
            class AClass(object):
                def amethod(self, other):
                    other.do_something()
                    self.

                def another(self):
                    pass
        """)
        klass, parents = infer(source, 5)
        self.assertEquals(klass, 'AClass')
        self.assertEquals(parents, ['object'])


    def testInferParents(self):
        source = dedent("""\
            import something
            from something import father as stepfather
            class AClass(something.mother, stepfather):
                def amethod(self, other):
                    other.do_something()
                    self.

                def another(self):
                    pass
        """)
        klass, parents = infer(source, 6)
        self.assertEquals(klass, 'AClass')
        self.assertEquals(parents, ['something.mother', 'something.father'])


    def testInferParentsTricky(self):
        source = dedent("""\
            from something.this import other as another
            class AClass(another.bother):
                def amethod(self, other):
                    other.do_something()
                    self.

                def another(self):
                    pass
        """)
        klass, parents = infer(source, 5)
        self.assertEquals(klass, 'AClass')
        self.assertEquals(parents, ['something.this.other.bother'])


    def testInferSelfMultipleClasses(self):
        
        source = dedent("""\
            import something
            class AClass(object):
                def amethod(self, other):
                    other.do_something()
                    class Sneak(object):
                        def sth(self):
                            class EvenSneakier(object):
                                pass
                            pass
                    pass

                def another(self):
                    pass



            class BClass(object):
                def newmethod(self, something):
                    wibble = [i for i in self.a]
                    pass

                def newerMethod(self, somethingelse):
                    if Bugger:
                        self.ass
        """)
        
        self.assertEquals(infer(source, 1)[0], None, 'no class yet!')
        for line in range(2, 5):
            klass, _ = infer(source, line)
            self.assertEquals(klass, 'AClass', 'wrong class %s in line %d' % (klass, line))

        for line in range(5, 7):
            klass, _ = infer(source, line)
            self.assertEquals(klass, 'Sneak', 'wrong class %s in line %d' % (klass, line))

        for line in range(7, 9):
            klass, _ = infer(source, line)
            self.assertEquals(klass, 'EvenSneakier', 'wrong class %s in line %d' % (klass, line))

        line = 9
        klass, _ = infer(source, line)
        self.assertEquals(klass, 'Sneak', 'wrong class %s in line %d' % (klass, line))

        for line in range(10, 17):
            klass, _ = infer(source, line)
            self.assertEquals(klass, 'AClass', 'wrong class %s in line %d' % (klass, line))

        for line in range(17, 51):
            klass, _ = infer(source, line)
            self.assertEquals(klass, 'BClass', 'wrong class %s in line %d' % (klass, line))
    

if __name__ == '__main__':
    unittest.main()

