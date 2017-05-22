import six

from capnpy import ptr
from capnpy.printer import print_buffer
from capnpy.visit import end_of, is_compact
from capnpy.segment.segment import Segment
from six import b

class TestEndOf(object):

    def end_of(self, buf, offset, data_size, ptrs_size):
        buf = Segment(buf)
        p = ptr.new_struct(0, data_size, ptrs_size)
        return end_of(buf, p, offset-8)

    def test_struct_data(self):
        buf = b('garbage0'
               'garbage1'
               '\x01\x00\x00\x00\x00\x00\x00\x00'  # 1
               '\x02\x00\x00\x00\x00\x00\x00\x00') # 2
        end = self.end_of(buf, 16, data_size=2, ptrs_size=0)
        assert end == 32

    def test_struct_ptrs(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ## }
        ##
        ## struct Rectangle {
        ##   color @0 :Int64;
        ##   a @1 :Point;
        ##   b @2 :Point;
        ## }
        buf = b('garbage0'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x0c\x00\x00\x00\x02\x00\x00\x00'    # ptr to a
               '\x10\x00\x00\x00\x02\x00\x00\x00'    # ptr to b
               'garbage1'
               'garbage2'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # a.x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'    # a.y == 2
               '\x03\x00\x00\x00\x00\x00\x00\x00'    # b.x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00')   # b.y == 4
        end = self.end_of(buf, 8, data_size=1, ptrs_size=2)
        #assert start == 48
        assert end == 80

    def test_struct_one_null_ptr(self):
        buf = b('\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x0c\x00\x00\x00\x02\x00\x00\x00'    # ptr to a
               '\x00\x00\x00\x00\x00\x00\x00\x00'    # ptr to b, NULL
               'garbage1'
               'garbage2'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # a.x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00')   # a.y == 2
        end = self.end_of(buf, 0, data_size=1, ptrs_size=2)
        #assert start == 40  # XXX
        assert end == 56

    def test_struct_all_null_ptrs(self):
        buf = b('\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x00\x00\x00\x00\x00\x00\x00\x00'    # ptr to a, NULL
               '\x00\x00\x00\x00\x00\x00\x00\x00')   # ptr to b, NULL
        end = self.end_of(buf, 0, data_size=1, ptrs_size=2)
        #assert start == 24 # XXX
        assert end == 24

    def test_list_primitive(self):
        buf = b('\x0d\x00\x00\x00\x1a\x00\x00\x00'   #  0: ptr list<8>  to a
               '\x0d\x00\x00\x00\x1b\x00\x00\x00'   #  8: ptr list<16> to b
               '\x0d\x00\x00\x00\x1c\x00\x00\x00'   # 16: ptr list<32> to c
               '\x11\x00\x00\x00\x1d\x00\x00\x00'   # 24: ptr list<64> to d
               '\x01\x02\x03\x00\x00\x00\x00\x00'   # 32: a = [1, 2, 3]
               '\x04\x00\x05\x00\x06\x00\x00\x00'   # 40: b = [4, 5, 6]
               '\x07\x00\x00\x00\x08\x00\x00\x00'   # 48: c = [7, 8, 9]
               '\x09\x00\x00\x00\x00\x00\x00\x00'   # 56:
               '\x0a\x00\x00\x00\x00\x00\x00\x00'   # 64: d = [10, 11, 12]
               '\x0b\x00\x00\x00\x00\x00\x00\x00'   # 72
               '\x0c\x00\x00\x00\x00\x00\x00\x00')  # 80
        end_a = self.end_of(buf, 0, data_size=0, ptrs_size=1)
        end_b = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        end_c = self.end_of(buf, 16, data_size=0, ptrs_size=1)
        end_d = self.end_of(buf, 24, data_size=0, ptrs_size=1)
        #assert body_start == ??? # XXX
        assert end_a == 32 + 3
        assert end_b == 40 + (3*2)
        assert end_c == 48 + (3*4)
        assert end_d == 64 + (3*8)

    def test_list_of_bool(self):
        buf = b('garbage1'
               '\x01\x00\x00\x00\x19\x00\x00\x00'    # ptrlist
               '\x03\x00\x00\x00\x00\x00\x00\x00')   # [True, True, False]
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        assert end == 17

    def test_list_composite(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x01\x00\x00\x00\x4f\x00\x00\x00'   # ptr to list
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x19\x00\x00\x00\x42\x00\x00\x00'   # points[0].name == ptr
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x11\x00\x00\x00\x42\x00\x00\x00'   # points[1].name == ptr
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x09\x00\x00\x00\x42\x00\x00\x00'   # points[2].name == ptr
               'P' 'o' 'i' 'n' 't' ' ' 'A' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'B' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'C' '\x00'
               'garbage1')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        assert end == 120
        assert buf[end:] == b'garbage1'

    def test_list_composite_one_null_ptr(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x01\x00\x00\x00\x4f\x00\x00\x00'   # ptr to list
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x19\x00\x00\x00\x42\x00\x00\x00'   # points[0].name == ptr
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x11\x00\x00\x00\x42\x00\x00\x00'   # points[1].name == ptr
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[2].name == NULL
               'P' 'o' 'i' 'n' 't' ' ' 'A' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'B' '\x00'
               'garbage1')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        assert end == 112
        assert buf[end:] == b'garbage1'

    def test_list_composite_all_null_ptrs(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x01\x00\x00\x00\x4f\x00\x00\x00'   # ptr to list
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[0].name == NULL
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[1].name == NULL
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[2].name == NULL
               'garbage1')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        assert end == 96
        assert buf[end:] == b'garbage1'

    def test_list_composite_no_ptr(self):
        buf = b('garbage0'
               '\x01\x00\x00\x00\x27\x00\x00\x00'   # ptr to list
               '\x08\x00\x00\x00\x02\x00\x00\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # p[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # p[0].y == 2
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # p[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # p[1].y == 4
               'garbage1'
               'garbage2')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        assert end == 56
        assert buf[end:] == b'garbage1garbage2'

    def test_list_of_pointers(self):
        buf = b('garbage0'
               '\x01\x00\x00\x00\x1e\x00\x00\x00'   # ptr to list
               '\x09\x00\x00\x00\x32\x00\x00\x00'   # strings[0] == ptr to #0
               '\x09\x00\x00\x00\x52\x00\x00\x00'   # strings[1] == ptr to #1
               '\x0d\x00\x00\x00\xb2\x00\x00\x00'   # strings[2] == ptr to #2
               'h' 'e' 'l' 'l' 'o' '\x00\x00\x00'   # #0
               'c' 'a' 'p' 'n' 'p' 'r' 'o' 't'      # #1...
               'o' '\x00\x00\x00\x00\x00\x00\x00'
               't' 'h' 'i' 's' ' ' 'i' 's' ' '      # #2...
               'a' ' ' 'l' 'o' 'n' 'g' ' ' 's'
               't' 'r' 'i' 'n' 'g' '\x00\x00\x00')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        # note that the end if 88, not 86: the last two \x00\x00 are not counted,
        # because they are padding, not actual data
        assert end == 86
        assert buf[end:] == b'\x00\x00'

    def test_list_of_pointers_all_null(self):
        buf = b('garbage0'
               '\x01\x00\x00\x00\x1e\x00\x00\x00'   # ptr to list
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               'garbage1')
        end = self.end_of(buf, 8, data_size=0, ptrs_size=1)
        #assert start == 16  # XXX
        # note that the end if 88, not 86: the last two \x00\x00 are not counted,
        # because they are padding, not actual data
        assert end == 40
        assert buf[end:] == b'garbage1'


class TestIsCompact(object):

    def is_compact(self, buf, offset, kind, **kwds):
        buf = Segment(buf)
        if kind == ptr.STRUCT:
            p = ptr.new_struct(0, **kwds)
        elif kind == ptr.LIST:
            p = ptr.new_list(0, **kwds)
        else:
            assert False
        return is_compact(buf, p, offset-8)

    def test_struct_data_only(self):
        buf = b('garbage0'
               'garbage1'
               '\x01\x00\x00\x00\x00\x00\x00\x00'  # 1
               '\x02\x00\x00\x00\x00\x00\x00\x00') # 2
        is_compact = self.is_compact(buf, 16, ptr.STRUCT, data_size=2, ptrs_size=0)
        assert is_compact

    def test_struct_ptrs_not_compact(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ## }
        ##
        ## struct Rectangle {
        ##   color @0 :Int64;
        ##   a @1 :Point;
        ##   b @2 :Point;
        ## }
        buf = b('garbage0'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x0c\x00\x00\x00\x02\x00\x00\x00'    # ptr to a
               '\x10\x00\x00\x00\x02\x00\x00\x00'    # ptr to b
               'garbage1'
               'garbage2'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # a.x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'    # a.y == 2
               '\x03\x00\x00\x00\x00\x00\x00\x00'    # b.x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00')   # b.y == 4
        is_compact = self.is_compact(buf, 8, ptr.STRUCT, data_size=1, ptrs_size=2)
        assert not is_compact

    def test_struct_ptrs_compact(self):
        buf = b('garbage0'
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x04\x00\x00\x00\x02\x00\x00\x00'    # ptr to a
               '\x08\x00\x00\x00\x02\x00\x00\x00'    # ptr to b
               '\x01\x00\x00\x00\x00\x00\x00\x00'    # a.x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'    # a.y == 2
               '\x03\x00\x00\x00\x00\x00\x00\x00'    # b.x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00')   # b.y == 4
        is_compact = self.is_compact(buf, 8, ptr.STRUCT, data_size=1, ptrs_size=2)
        assert is_compact

    def test_struct_all_null_ptrs(self):
        buf = b('\x01\x00\x00\x00\x00\x00\x00\x00'    # color == 1
               '\x00\x00\x00\x00\x00\x00\x00\x00'    # ptr to a, NULL
               '\x00\x00\x00\x00\x00\x00\x00\x00')   # ptr to b, NULL
        is_compact = self.is_compact(buf, 0, ptr.STRUCT, data_size=1, ptrs_size=2)
        assert is_compact

    def test_list_primitive(self):
        buf = b'\x01\x02\x03\x00\x00\x00\x00\x00'   # 32: list<8> [1, 2, 3]
        is_compact = self.is_compact(buf, 0, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_8,
                                     item_count=3)
        assert is_compact

    def test_list_of_bool(self):
        buf = b'\x03\x00\x00\x00\x00\x00\x00\x00'   # [True, True, False]
        is_compact = self.is_compact(buf, 0, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_BIT,
                                     item_count=3)
        assert is_compact

    def test_list_composite_compact(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x19\x00\x00\x00\x42\x00\x00\x00'   # points[0].name == ptr
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x11\x00\x00\x00\x42\x00\x00\x00'   # points[1].name == ptr
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x09\x00\x00\x00\x42\x00\x00\x00'   # points[2].name == ptr
               'P' 'o' 'i' 'n' 't' ' ' 'A' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'B' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'C' '\x00'
               'garbage1')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_COMPOSITE,
                                     item_count=3)
        assert is_compact

    def test_list_composite_not_compact(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x1d\x00\x00\x00\x42\x00\x00\x00'   # points[0].name == ptr
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x15\x00\x00\x00\x42\x00\x00\x00'   # points[1].name == ptr
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x0d\x00\x00\x00\x42\x00\x00\x00'   # points[2].name == ptr
               'garbage1'
               'P' 'o' 'i' 'n' 't' ' ' 'A' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'B' '\x00'
               'P' 'o' 'i' 'n' 't' ' ' 'C' '\x00'
               'garbage2')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_COMPOSITE,
                                     item_count=3)
        assert not is_compact


    def test_list_composite_nullptr(self):
        ## struct Point {
        ##   x @0 :Int64;
        ##   y @1 :Int64;
        ##   name @2 :Text;
        ## }
        buf = b('garbage0'
               '\x0c\x00\x00\x00\x02\x00\x01\x00'   # list tag
               '\x01\x00\x00\x00\x00\x00\x00\x00'   # points[0].x == 1
               '\x02\x00\x00\x00\x00\x00\x00\x00'   # points[0].y == 2
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[0].name == NULL
               '\x03\x00\x00\x00\x00\x00\x00\x00'   # points[1].x == 3
               '\x04\x00\x00\x00\x00\x00\x00\x00'   # points[1].y == 4
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[1].name == NULL
               '\x05\x00\x00\x00\x00\x00\x00\x00'   # points[2].x == 5
               '\x06\x00\x00\x00\x00\x00\x00\x00'   # points[2].y == 6
               '\x00\x00\x00\x00\x00\x00\x00\x00'   # points[2].name == NULL
               'garbage1')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_COMPOSITE,
                                     item_count=3)
        assert is_compact

    def test_list_of_pointers_compact(self):
        buf = b('garbage0'
               '\x09\x00\x00\x00\x32\x00\x00\x00'   # strings[0] == ptr to #0
               '\x09\x00\x00\x00\x52\x00\x00\x00'   # strings[1] == ptr to #1
               '\x0d\x00\x00\x00\xb2\x00\x00\x00'   # strings[2] == ptr to #2
               'h' 'e' 'l' 'l' 'o' '\x00\x00\x00'   # #0
               'c' 'a' 'p' 'n' 'p' 'r' 'o' 't'      # #1...
               'o' '\x00\x00\x00\x00\x00\x00\x00'
               't' 'h' 'i' 's' ' ' 'i' 's' ' '      # #2...
               'a' ' ' 'l' 'o' 'n' 'g' ' ' 's'
               't' 'r' 'i' 'n' 'g' '\x00\x00\x00')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_PTR,
                                     item_count=3)
        assert is_compact

    def test_list_of_pointers_not_compact(self):
        buf = b('garbage0'
               '\x0d\x00\x00\x00\x32\x00\x00\x00'   # strings[0] == ptr to #0
               '\x0d\x00\x00\x00\x52\x00\x00\x00'   # strings[1] == ptr to #1
               '\x11\x00\x00\x00\xb2\x00\x00\x00'   # strings[2] == ptr to #2
               'garbage1'
               'h' 'e' 'l' 'l' 'o' '\x00\x00\x00'   # #0
               'c' 'a' 'p' 'n' 'p' 'r' 'o' 't'      # #1...
               'o' '\x00\x00\x00\x00\x00\x00\x00'
               't' 'h' 'i' 's' ' ' 'i' 's' ' '      # #2...
               'a' ' ' 'l' 'o' 'n' 'g' ' ' 's'
               't' 'r' 'i' 'n' 'g' '\x00\x00\x00')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_PTR,
                                     item_count=3)
        assert not is_compact

    def test_list_of_pointers_all_null(self):
        buf = b('garbage0'
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               '\x00\x00\x00\x00\x00\x00\x00\x00'
               'garbage1')
        is_compact = self.is_compact(buf, 8, ptr.LIST,
                                     size_tag=ptr.LIST_SIZE_PTR,
                                     item_count=3)
        assert is_compact
