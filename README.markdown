#PySmell

PySmell is a python IDE completion helper. 

It tries to statically analyze Python source code, without executing it,
and generates information about a project's structure that IDE tools can
use.

There is currently support for Vim, Emacs and TextMate. Feel free to contribute
your own favourite editor bindings, or to improve the existing ones.

##Download and Installation

Run the following commands (without $ preceding)
$ git clone git://github.com/rohdef/pysmell.git
(Warning! Do not do 'reset --hard' if you modified the original source, it will overwrite those changes!)
$ git reset --hard HEAD

### For library use

+ There's two ways to use this, if you want to import it as a part of your own Python project go to 
the cloned pysmell, and copy the pysmell subdirectory to you project. From there you can use it as 
follows:

	from pysmell.tags import process
	from pysmell.outputHandlers.EvalParser import EvalParser
	from pysmell.outputHandlers.PrintOut import PrintOut
	
	def parsePythonCode(fileList):
	    """
	    Parse a list of files into a module directionary for further parsing,
	    then send the modules to an EvalParser (uses pretty print aka pprint)
	    which is set to use PrintOut for wrting its contents. Finally do the 
	    write to actually run the parsing and printing.
	    """
	    modules = process(fileList)
	    parser = EvalParser(PrintOut())
	    parser.write(modules)

More parsers and out systems can be found in the outputHandlers directory, and more 
examples can be found in runPySmell.py

+ The second way is if you want pysmell to run as a kind of service for another programming language 
or independantly in another way. In this case modify runPySmell.py to your needs.

### For application (original) use

The original PySmell is available at [PyPI](http://pypi.python.org/pypi/pysmell).

In the source directory do:
**On Ubuntu and similar \*nix systems:**
$ sudo setup.py install
**Other \*nix systems**
\# python setup.py install

You should be able to `import pysmell` inside your Python interpreter and invoke
`pysmell` at the command line.

You can track the development of PySmell by visiting 
[GitHub](http://github.com/orestis/pysmell/). You can click 'Download'
to get it as a zip/tar if you don't have git installed. `python setup.py
develop` will setup your enviroment.

##Usage

**These usage instructions is for the original pysmell setup**

Before you invoke PySmell, you need to generate a PYSMELLTAGS file: 

    cd /root/of/project
    pysmell .

If you want to specifically include or exclude some files or directories
(eg. tests), you can use: 

    pysmell [Package Package File File ...] [-x Excluded Excluded ...]

Check for more options by invoking `pysmell` without any arguments

##Using external libraries

PySmell can handle completions of external libraries, like the Standard
Library and Django. 

To use external libraries, you have to first analyze the libraries you
want, eg. for stdlib:

    pysmell . -x site-packages test -o ~/PYSMELLTAGS.stdlib

This will create PYSMELLTAGS.stdlib in your HOME. Copy that in the root
of your project, and repeat for other libraries by changing the
extension. Note that you still have to have a root PYSMELLTAGS file with
no extension at the very root of your project.

##Partial tags

Sometimes it's useful to not pollute global namespaces with tags of
sub-projects. For example, assume that there is a Tests package, which
has hundreds of tests, together with a few testing-related modules. You
only want to see these completions when working on test file.

To accomplish that, you can put PYSMELLTAGS.* files inside
subdirectories, and they will be used only when you're working on a file
somewhere in that directory or its children.*

    pysmell Tests/FunctionalTest.py Tests/UndoTestCase.py -o Tests/PYSMELLTAGS.Tests

The information in FunctionalTest and UndoTestCase will only be
accessible when editing a file inside the Tests package.

##Vim

To use PySmell omnicompletion from inside Vim, you have to have:

1. Python support in vim (`:echo has('python')`)
2. The pysmell package in the PYTHONPATH that Vim uses: `python import pysmell` should work.
3. Drop pysmell.vim in ~/.vim/plugin
4. `:setlocal omnifunc=pysmell#Complete` Note: If you want to always use pysmell for
python, do: `autocmd FileType python setlocal omnifunc=pysmell#Complete`
5. [OPTIONAL] Select a matcher of your liking - look at pysmell.vim for
options. Eg: `:let g:pysmell_matcher='camel-case'`

You can then use ^X^O to invoke Vim's omnicompletion.

You can generate debugging information by doing:

    :let g:pysmell_debug=1
    :e PYSMELL_DEBUG

Debug information will be appended in that buffer, copy and paste it
into the report.

##TextMate

Double-click PySmell.tmbundle :)

Complete with alt-esc - look into the bundle for more commands.

You can find the bundle in the source distribution - it's not installed
with the egg, because it's too much trouble. 

Set TM\_PYTHON in your Shell Variables to point to the Python where you
installed PySmell.

##Emacs

Put pysmell.el into your `load-path`, and inside your .emacs file put:

    (require 'pysmell)
    (add-hook 'python-mode-hook (lambda () (pysmell-mode 1)))

Complete with M-/, create tags with M-x pysmell-make-tags

[Pymacs](http://pymacs.progiciels-bpi.ca/) is required as well.

# Authors and license
This is currently maintained by Rohde Fischer (rohdef@rohdef.dk) - github.com/rohdef

## The original authors and contributers
Orestis Markou (orestis@orestis.gr) - github.com/orestis (original author)
Krzysiek Goj - github.com/goj
Werner Mendizabal (nonameentername@gmail.com) - github.com/nonameentername
Alec Thomas (alec@swapoff.org) - github.com/alecthomas
Michael Thalmeier - github.com/mthalmei
Tom Wright (tat.wright@tat.wright.name)
Jaime Wyant (programmer.py@gmail.com)

## License 
Copyright 2011 Rohde Fischer (rohdef@rohdef.dk). All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY ROHDE FISCHER ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ROHDE FISCHER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Rohde Fischer.

#Reporting issues

Please report issues and bugs at https://github.com/rohdef/pysmell/issues 
I will try to fix them at the best of my abilities. I didn't write this to 
start with, so I won't promise anything.

If you can create a unit test that exposes that behaviour, it'd be great!


The original PySmell is hosted at [Google Code](http://code.google.com/p/pysmell).
