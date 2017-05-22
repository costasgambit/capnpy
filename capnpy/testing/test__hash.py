import py
import sys
from pypytools import IS_PYPY
from capnpy.util import PY3
from capnpy import _hash

def test_inthash():
    h = _hash.inthash
    assert h(42) == hash(42)
    assert h(-1) == hash(-1)
    assert h(-2) == hash(-2)
    assert h(sys.maxsize) == hash(sys.maxsize)
    assert h(-sys.maxsize-1) == hash(-sys.maxsize-1)

def test_longhash():
    h = _hash.longhash
    # these are easy
    assert h(42) == hash(42)
    assert h(sys.maxsize) == hash(sys.maxsize)
    #
    # these are real longs
    assert h(sys.maxsize+1) == hash(sys.maxsize+1)
    maxulong = sys.maxsize*2 + 1
    assert h(maxulong) == hash(maxulong)
    if not PY3:
        assert hash(maxulong) == hash(-1)

def test_strhash():
    expected_hash_empty_string = 0
    if IS_PYPY:
        expected_hash_empty_string = -2
    #
    h = _hash.strhash
    assert h('', 0, 0) == hash('') == expected_hash_empty_string
    assert h('hello', 0, 5) == hash('hello')
    assert h('hello', 1, 4) == hash('ello')
    assert h('hello', 1, 3) == hash('ell')
    assert h('hello', 1, 100) == hash('ello')
    assert h('hello', 1, 0) == hash('')
    assert h('hello', 100, 5) == hash('')

def test_tuplehash():
    h = _hash.__tuplehash_for_tests
    assert h((42,)) == hash((42,))
    assert h((42, 43)) == hash((42, 43))
    assert h((42, 43, 44)) == hash((42, 43, 44))
