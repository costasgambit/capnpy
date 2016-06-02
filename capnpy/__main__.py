import sys
import py
import time
from capnpy import load_schema
from capnpy.message import load
from capnpy.compiler.compiler import StandaloneCompiler


def decode(argv):
    filename = argv[2]
    schemaname = argv[3]
    clsname = argv[4]
    print >> sys.stderr, 'Loading schema...'
    a = time.time()
    mod = load_schema(schemaname, convert_case=False)
    b = time.time()
    print >> sys.stderr, 'schema loaded in %.2f secs' % (b-a)
    print >> sys.stderr, 'decoding stream...'
    cls = getattr(mod, clsname)
    with open(filename) as f:
        i = 0
        while True:
            try:
                obj = load(f, cls)
            except ValueError:
                break
            print obj.shortrepr()
            i += 1
            if i % 10000 == 0:
                print >> sys.stderr, i
    c = time.time()
    print >> sys.stderr, 'stream decoded in %.2f secs' % (c-b)

def compile(argv):
    srcfile = argv[2]
    if '--pyx' in argv:
        pyx = True
    elif '--pyx=no' in argv:
        pyx = False
    else:
        pyx = 'auto'
    #
    convert_case = True
    if '--convert-case=no' in argv:
        convert_case = False
    #
    comp = StandaloneCompiler(sys.path)
    comp.compile(srcfile, convert_case=convert_case, pyx=pyx)

def main(argv=sys.argv):
    cmd = argv[1]
    if cmd == 'decode':
        decode(argv)
    elif cmd == 'compile':
        compile(argv)
    else:
        print 'usage: python -m capnpy decode|compile [ARGS]'

if __name__ == '__main__':
    main()
