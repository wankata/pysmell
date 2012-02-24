from subprocess import *
import os
import sys
sys.path.append(os.path.abspath(os.path.curdir))
import settings

def run(command):
    proc = Popen(command.split(' '), stdout=PIPE)
    output = proc.communicate()[0]
    if output.strip():
        print output

def rmtags():
    for root, dirs, files in os.walk('.'):
        for name in files:
            if name.startswith('PYSMELLTAGS') or name == 'tags':
                run('rm {0}'.format(name))

def mktags():
    rmtags()

    path = '{0}/lib/python{1.major}.{1.minor}/site-packages'.format(os.environ['VIRTUAL_ENV'], sys.version_info)
    #packages = ['fabric', ]

    for package in settings.packages:
        run('ctags -aR %(path)s/%(package)s' % locals())
        run('pysmell -o PYSMELLTAGS.%(package)s %(path)s/%(package)s' % locals())

    run('ctags -aR .')
    run('pysmell .')
