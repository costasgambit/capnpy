from capnpy import ptr

class Visitor(object):
    """
    Generic logic for visiting an arbitrary capnp object.
    """

    def visit(self, buf, p, offset):
        kind = ptr.kind(p)
        offset = ptr.deref(p, offset)
        if kind == ptr.STRUCT:
            data_size = ptr.struct_data_size(p)
            ptrs_size = ptr.struct_ptrs_size(p)
            return self.visit_struct(buf, p, offset, data_size, ptrs_size)
        elif kind == ptr.LIST:
            item_size = ptr.list_size_tag(p)
            count = ptr.list_item_count(p)
            if item_size == ptr.LIST_SIZE_COMPOSITE:
                tag = buf.read_ptr(offset)
                count = ptr.offset(tag)
                data_size = ptr.struct_data_size(tag)
                ptrs_size = ptr.struct_ptrs_size(tag)
                return self.visit_list_composite(buf, p, offset,
                                                  count, data_size, ptrs_size)
            elif item_size == ptr.LIST_SIZE_PTR:
                return self.visit_list_ptr(buf, p, offset, count)
            elif item_size == ptr.LIST_SIZE_BIT:
                return self.visit_list_bit(buf, p, offset, count)
            else:
                return self.visit_list_primitive(buf, p, offset, item_size, count)
        elif kind == ptr.FAR:
            raise NotImplementedError('Far pointer not supported')
        else:
            assert False, 'unknown ptr kind'

    def visit_struct(self, buf, p, offset, data_size, ptrs_size):
        raise NotImplementedError

    def visit_list_composite(self, buf, p, offset, count, data_size, ptrs_size):
        raise NotImplementedError

    def visit_list_ptr(self, buf, p, offset, count):
        raise NotImplementedError

    def visit_list_primitive(self, buf, p, offset, item_size, count):
        raise NotImplementedError

    def visit_list_bit(self, buf, p, offset, count):
        raise NotImplementedError


class EndOf(Visitor):
    """
    Find the end boundary of the object pointed by p.
    This assumes that the buffer is in pre-order.
    """

    def visit_ptrs(self, buf, offset, ptrs_size):
        i = ptrs_size
        while i > 0:
            i -= 1
            p2_offset = offset + i*8
            p2 = buf.read_ptr(p2_offset)
            if p2:
                return self.visit(buf, p2, p2_offset)
        return -1

    def visit_struct(self, buf, p, offset, data_size, ptrs_size):
        offset += data_size*8
        end = self.visit_ptrs(buf, offset, ptrs_size)
        if end != -1:
            return end
        return offset + (ptrs_size*8)

    def visit_list_composite(self, buf, p, offset, count, data_size, ptrs_size):
        item_size = (data_size+ptrs_size)*8
        offset += 8
        if ptrs_size:
            i = count
            while i > 0:
                i -= 1
                item_offset = offset + (item_size)*i + (data_size*8)
                end = self.visit_ptrs(buf, item_offset, ptrs_size)
                if end != -1:
                    return end
        # no ptr found
        return offset + (item_size)*count

    def visit_list_ptr(self, buf, p, offset, count):
        end = self.visit_ptrs(buf, offset, count)
        if end != -1:
            return end
        return offset + 8*count

    def visit_list_primitive(self, buf, p, offset, item_size, count):
        item_size = ptr.list_item_length(item_size)
        return offset + item_size*count

    def visit_list_bit(self, buf, p, offset, count):
        bytes_length = count // 8
        extra_bits = count % 8
        if extra_bits:
            bytes_length += 1
        return offset + bytes_length


class IsCompact(Visitor):
    """
    Determines whether the object pointed by p is "compact", i.e. when its
    first children starts immediately after its body. This assumes the buffer
    is in pre-order.
    """

    def start_of_ptrs(self, buf, offset, ptrs_size):
        i = 0
        while i < ptrs_size:
            p2_offset = offset + i*8
            p2 = buf.read_ptr(p2_offset)
            if p2:
                return ptr.deref(p2, p2_offset)
            i += 1
        return -1

    def visit_struct(self, buf, p, offset, data_size, ptrs_size):
        """
        A struct is compact if its first non-null pointer points immediately after
        the end of its body.
        """
        end_of_body = offset + (data_size+ptrs_size)*8
        offset += data_size*8
        start_of_children = self.start_of_ptrs(buf, offset, ptrs_size)
        return start_of_children == -1 or start_of_children == end_of_body

    def visit_list_primitive(self, buf, p, offset, item_size, count):
        return True

    def visit_list_bit(self, buf, p, offset, count):
        return True

    def visit_list_composite(self, buf, p, offset, count, data_size, ptrs_size):
        offset += 8
        item_size = (data_size+ptrs_size)*8
        end_of_items = offset + item_size*count
        if ptrs_size:
            i = 0
            while i < count:
                item_offset = offset + (item_size)*i + (data_size*8)
                start_of_children = self.start_of_ptrs(buf, item_offset, ptrs_size)
                if start_of_children != -1:
                    return start_of_children == end_of_items
                i += 1
        # no ptr found
        return True

    def visit_list_ptr(self, buf, p, offset, count):
        end_of_items = offset + count*8
        start_of_children = self.start_of_ptrs(buf, offset, count)
        return start_of_children == -1 or start_of_children == end_of_items


def end_of(buf, p, offset):
    return _end_of.visit(buf, p, offset)

def is_compact(buf, p, offset):
    return _is_compact.visit(buf, p, offset)

_end_of = EndOf()
_is_compact = IsCompact()
