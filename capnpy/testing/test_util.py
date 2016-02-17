import py
import textwrap
from capnpy.util import extend, extend_module_maybe

def test_extend():
    class Foo(object):
        pass

    @extend(Foo)
    class Bar(object):
        a = 42
        def foo(self):
            return 123

    assert Bar is Foo
    assert Foo.a == 42
    assert Foo().foo() == 123


@py.test.mark.usefixtures('init')
class TestExtendModuleMaybe(object):

    @py.test.fixture
    def init(self, tmpdir):
        self.tmpdir = tmpdir

    def w(self, filename, src):
        src = textwrap.dedent(src)
        self.tmpdir.join(filename).write(src)

    def test_filename_simple(self):
        self.w("foo_extended.py", """
            answer = 42
        """)
        #
        myglobals = {}
        extend_module_maybe(myglobals, filename=self.tmpdir.join('foo.py'))
        assert myglobals['answer'] == 42

    def test_filename_dont_exist(self):
        myglobals = {}
        extend_module_maybe(myglobals, filename=self.tmpdir.join('foo.py'))
        assert myglobals == {}

    def test_modname_simple(self, monkeypatch):
        monkeypatch.syspath_prepend(self.tmpdir)
        self.w("foo_extended.py", """
            answer = 42
        """)
        #
        myglobals = {}
        extend_module_maybe(myglobals, modname='foo')
        assert myglobals['answer'] == 42
