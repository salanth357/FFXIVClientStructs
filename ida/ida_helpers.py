from abc import abstractmethod
from typing import Any

import idaapi
import ida_typeinf
import idc
import ida_bytes
import ida_ida
import ida_funcs
import ida_name
import ida_search

is_ida_9 = idaapi.IDA_SDK_VERSION >= 900
size_scale = 8 if is_ida_9 else 1

def is_signed(type):
    # type: (str) -> bool
    if (
        type == "__int8"
        or type == "__int16"
        or type == "__int32"
        or type == "__int64"
        or type == "int"
        or type == "_DWORD"
    ):
        return True
    else:
        return False
def get_tinfo_by_tid(tid):
    #type: (int) -> idaapi.tinfo_t
    tif = ida_typeinf.tinfo_t()
    if tif.get_type_by_tid(tid):
        return tif
    return None

def get_struc_tinfo_by_tid(struct_tid):
    #type: (int) -> idaapi.tinfo_t
    tif = get_tinfo_by_tid(struct_tid)
    if tif is not None and (tif.is_struct() or tif.is_union()):
        return tif
    return None

def clean_struct_name(name):
    # type: (str) -> str
    if name == "Tm":
        return "tm" # tm is a keyword in IDA for the time struct but C# exports it as Tm
    return (
        name.replace(" ", "")
        .replace("unsigned", "u")
        .replace("__int64", "long")
        .replace("__int32", "int")
        .replace("__int16", "short")
        .replace("__int8", "byte")
    )
    
def get_named_type(name):
    # type: (str) -> idaapi.tinfo_t
    tinfo = ida_typeinf.tinfo_t()
    clean_name = clean_struct_name(name)
    if (
        idc.get_struc_id(clean_name)
        != idaapi.BADADDR
        or 
        idc.get_enum(clean_name)
        != idaapi.BADADDR
    ):
        if not tinfo.get_named_type(idaapi.get_idati(), clean_name):
            raise ValueError("{0} not found in IDA database".format(clean_name))
            
        return tinfo


    if name == "void":
        idaapi.parse_decl(
            tinfo, idaapi.get_idati(), "void (__fastcall)();", idaapi.PT_SIL
        )
        return tinfo.get_rettype()

    terminated = name + ";"
    idaapi.parse_decl(tinfo, idaapi.get_idati(), terminated, idaapi.PT_SIL)

    tinfo_str = tinfo.dstr()
    if tinfo_str == name or tinfo_str == clean_name:
        return tinfo

    terminated = clean_name + ";"
    idaapi.parse_decl(tinfo, idaapi.get_idati(), terminated, idaapi.PT_SIL)
    return tinfo

def get_tinfo_from_type(raw_type, array_size=0):
    # type: (str, int) -> idaapi.tinfo_t
    """
    Retrieve a tinfo_t from a raw type string.
    """

    type = raw_type.rstrip("*")
    ptr_count = len(raw_type) - len(type)

    type_tinfo = get_named_type(type)

    ptr_tinfo = None
    if ptr_count > 0:
        for i in range(ptr_count):
            ptr_tinfo = idaapi.tinfo_t()
            if not ptr_tinfo.create_ptr(type_tinfo):
                print("! failed to create pointer")
                return None
            type_tinfo = ptr_tinfo
    else:
        ptr_tinfo = type_tinfo

    if array_size > 0:
        array_tinfo = idaapi.tinfo_t()
        if not array_tinfo.create_array(ptr_tinfo, array_size):
            print("! failed to create array")
            return None

        ptr_tinfo = array_tinfo

    return ptr_tinfo

def get_idc_type_from_ida_type(type):
    # type: (str) -> int
    if (
        type == "unsigned __int8"
        or type == "__int8"
        or type == "bool"
        or type == "char"
        or type == "unsigned char"
        or type == "byte"
    ):
        return ida_bytes.byte_flag()
    elif type == "unsigned __int16" or type == "__int16" or type == "wchar_t":
        return ida_bytes.word_flag()
    elif (
        type == "unsigned __int32"
        or type == "__int32"
        or type == "int"
        or type == "unsigned int"
        or type == "_DWORD"
    ):
        return ida_bytes.dword_flag()
    elif (
        type == "unsigned __int64"
        or type == "__int64"
        or type == "__fastcall"
        or type.endswith("*")
    ):
        return ida_bytes.qword_flag()
    elif type == "float":
        return ida_bytes.float_flag()
    elif type == "double":
        return ida_bytes.double_flag()
    elif idc.get_struc_id(type) == idaapi.BADADDR:
        return ida_bytes.enum_flag()
    else:
        return ida_bytes.stru_flag()
    
def search_binary(ea, pattern, flag=ida_bytes.BIN_SEARCH_FORWARD|ida_bytes.BIN_SEARCH_NOSHOW):
    # type: (int, str, int) -> int
    return ida_bytes.find_bytes(pattern, ea, range_end=ida_ida.inf_get_max_ea(), flags=flag)

udm_t = ida_typeinf.udm_t if is_ida_9 else ida_typeinf.udt_member_t
def create_udm(name, offset, typ):
    # type: (str, int, idaapi.tinfo_t) -> idaapi.udm_t
    udm = udm_t()
    udm.name = name
    udm.offset = offset*size_scale
    udm.type = typ
    udm.size = typ.get_size()*size_scale
    return udm

def get_idc_type_from_size(size):
    # type: (int) -> int
    if size == 1:
        return ida_bytes.byte_flag()
    elif size >= 2 and size < 4:
        return ida_bytes.word_flag()
    elif size >= 4 and size < 8:
        return ida_bytes.dword_flag()
    else:
        return ida_bytes.qword_flag()

def get_idc_type_from_size(size, offset=0):
    # type: (int, int) -> int
    if offset % 8 == 0 and size >= 8:
        return ida_bytes.qword_flag()
    elif offset % 4 == 0 and size >= 4:
        return ida_bytes.dword_flag()
    elif offset % 2 == 0 and size >= 2:
        return ida_bytes.word_flag()
    else:
        return ida_bytes.byte_flag()

def get_size_from_idc_type(type):
    # type: (int) -> int
    if type == ida_bytes.byte_flag():
        return 1
    elif type == ida_bytes.word_flag():
        return 2
    elif type == ida_bytes.dword_flag():
        return 4
    elif type == ida_bytes.qword_flag():
        return 8
    elif type == ida_bytes.float_flag():
        return 4
    elif type == ida_bytes.double_flag():
        return 8
    else:
        return 0

def opTypeAsName(n):
    for item in [x for x in dir(idc) if x.startswith("o_")]:
        if getattr(idc, item) == n:
            return item

def get_func_ea_by_sig(pattern):
    # type: (str) -> int
    ea = search_binary(0, pattern, ida_search.SEARCH_DOWN)

    if ida_funcs.get_func(ea) is None:
        finf = ida_funcs.func_t()
        finf.start_ea = ea
        finf.end_ea = idc.BADADDR
        ida_funcs.add_func_ex(finf)

    if ida_funcs.get_func(ea) is None:
        return idc.BADADDR

    if ida_funcs.get_func(ea).start_ea == ea:
        return ea
    mnem = idc.print_insn_mnem(ea)
    if not mnem:
        return idc.BADADDR

    opType0 = idc.get_operand_type(ea, 0)
    if mnem == "jmp" or mnem == "call" or mnem[0] == "j":
        if opType0 != idc.o_near and opType0 != idc.o_mem:
            print(
                "Error: Can't follow opType0 {0}".format(
                    opTypeAsName(opType0)
                )
            )
            return idc.BADADDR
        return idc.get_operand_value(ea, 0)

    if idc.next_head(ea) == ea + idc.get_item_size(ea) and idc.is_flow(
        idc.get_full_flags(idc.next_head(ea))
    ):
        return idc.next_head(ea)

def get_func_ea_by_name(name):
    # type: (str) -> int
    return ida_name.get_name_ea(0, name)





class BaseIdaStruct(object):
    def __init__(self, name):
        # type: (str) -> None
        self.name = name
        self._tif = None
    
    @abstractmethod
    def load_struct(self):
        pass

    @abstractmethod
    def delete_members(self):
        # type: (None) -> None
        pass
        

def get_padding_size(size, offset=0):
    if offset % 8 == 0 and size >= 8:
        return ("_QWORD", 8)
    elif offset % 4 == 0 and size >= 4:
        return ("_DWORD", 4)
    elif offset % 2 == 0 and size >= 2:
        return ("_WORD", 2)
    else:
        return ("_BYTE", 1)


if is_ida_9:
    class IdaEnum(object):
        def __init__(self, name):
            self.name = name
            self._tif = None
        
        @property
        def tif(self):
            # type: (None) -> ida_typeinf.tinfo_t
            if self._tif is None:
                self.load_enum()
            print(self._tif)
            return self._tif

        @tif.setter
        def tif(self, value):
            self._tif = value

        def load_enum(self):
            tif = get_named_type(self.name)
            if tif.is_enum():
                self.tif = tif
            else:
                self.tif = None

        def create_enum(self, underlying):
            if self.tif is None:
                print(self.name)
                idc.add_enum(idc.BADADDR, self.name, 0)
                self.tif.set_enum_width(get_size_from_idc_type(get_idc_type_from_ida_type(underlying)))
                self.tif.set_enum_sign(is_signed(underlying))

        def add_member(self, name, value):
            edm = ida_typeinf.edm_t()
            edm.name = "{0}.{1}".format(self.name, name)
            edm.value = value
            self.tif.add_edm(edm)

        def delete_members(self):
            if self.tif is None:
                return
            self.tif.del_edms(0, 0xFFFFFFFF)
else: # IDA < 9
    import ida_enum
    import ida_struct

    class IdaEnum(object):
        def __init__(self, name):
            self.name = name
            self._enum = None
        
        @property
        def enum(self):
            # type: (None) -> ida_typeinf.tinfo_t
            if self._enum is None:
                self.load_enum()
            return self._enum

        @enum.setter
        def enum(self, value):
            self._enum = value

        def load_enum(self):
            en = ida_enum.get_enum(self.name)
            if en != idaapi.BADADDR:
                self.enum = en
            else:
                self.enum = None

        def create_enum(self, underlying):
            if self.enum is None:
                ida_enum.add_enum(idc.BADADDR, self.name, 0)
                ida_enum.set_enum_width(self.enum, get_size_from_idc_type(underlying))
                ida_enum.set_enum_flag(self.enum, ida_enum.get_enum_flag(self.enum)|ida_bytes.FF_SIGN)

        def add_member(self, name, value):
            ida_enum.add_enum_member(self.enum, "{0}".format(name), value)

        def delete_members(self):
            if self.enum is None:
                return
            f = ida_enum.get_first_enum_member(self.enum)
            while f != idaapi.BADADDR:
                mem = ida_enum.get_enum_member(self.enum, f, -1, 0)
                ida_enum.del_enum_member(self.enum, f, 
                                         ida_enum.get_enum_member_serial(mem),
                                         ida_enum.get_enum_member_bmask(mem))
                f = ida_enum.get_first_enum_member(self.enum)

class IdaStruct(BaseIdaStruct):
    @property
    def tif(self):
        # type: () -> ida_typeinf.tinfo_t
        if self._tif is None:
            self.load_struct()
        return self._tif

    @tif.setter
    def tif(self, value):
        self._tif = value

    def load_struct(self):
        tif = get_named_type(self.name)
        if tif.is_struct() or tif.is_union():
            self.tif = tif
        else:
            self.tif = None
    
    def create_struct(self, is_union):
        if self.tif is None:
            idc.add_struc(-1, self.name, is_union)

    def has_member_at(self, offset):
        # type: (int) -> bool
        return idc.get_member_id(self.tif.get_tid(), offset) != -1

    def add_member(self, field_name, offset, field_type, is_baseclass = False, is_vtable = False, size = 0):
        ft = get_tinfo_from_type(field_type, size)
        udm = self.tif.get_udm_by_offset(offset)[1]
        if udm is not None and udm.type == ft:
            return None

        udm = create_udm(field_name, offset, ft)
        if is_baseclass:
            udm.set_baseclass()
        if is_vtable:
            udm.set_vftable()
        return self.add_udm(udm)

    if is_ida_9:
        def add_udm(self, udm):
            return self.tif.add_udm(udm)
    else:
        def add_udm(self, udm):
            udt = ida_typeinf.udt_type_data_t()
            self.tif.get_udt_details(udt)
            udt.push_back(udm)
            return self.tif.set_named_type(self.tif.get_til(), self.tif.get_type_name(), ida_typeinf.NTF_REPLACE)

    def add_vfunc(self, virt_func):
        print("add_vfunc", self.name, virt_func.name, virt_func.offset)
        offset = virt_func.offset
        field_name = virt_func.name
        
        if virt_func.return_type is None or virt_func.parameters is None:
            return
        
        ftd = ida_typeinf.func_type_data_t()
        ftd.cc = ida_typeinf.CM_CC_FASTCALL
        ftd.rettype = get_tinfo_from_type(virt_func.return_type)

        for param in virt_func.parameters:
            fa = ida_typeinf.funcarg_t()
            fa.name = param.name
            fa.type = get_tinfo_from_type(param.type)
            ftd.add_unique(fa)
        
        fti = ida_typeinf.tinfo_t()
        fti.create_func(ftd)
        fti = idaapi.make_pointer(fti)

        self.tif.add_udm(create_udm(field_name, offset, fti))

    @property
    def size(self):
        return self.tif.get_unpadded_size()*size_scale

    def pad_to(self, offset, fullpad):
        while offset > self.size:
            prev_size = self.size
            print("padding", self.name, prev_size, offset)
            if fullpad:
                typ, size = get_padding_size(prev_size)
                if size > offset - prev_size:
                    typ, size = get_padding_size(offset-prev_size, prev_size)
                size = 0
            else:
                typ, size = ("_BYTE", offset-prev_size)
            udm = ida_typeinf.udm_t()
            udm.offset = prev_size
            udm.type = get_tinfo_from_type(typ, size)
            udm.size = udm.type.get_size()*8
            udm.name = "field_{0:X}".format(prev_size)
            self.add_udm(udm)

    if is_ida_9:
        def delete_members(self):
            if self.tif is not None:
                self.tif.del_udms(0, self.tif.get_udt_nmembers())

        def delete(self):
            if self.tif is not None:
                ida_typeinf.del_numbered_type(None, self.tif.get_ordinal())
    else:
        def delete_members(self):
            s = ida_struct.get_struc(ida_struct.get_struc_id(self.name))
            ida_struct.del_struc_members(s, 0, -1)

# else:
#     class IdaStruct(object):
#        @property
#         def tif(self):
#             if self._tif is None:
#                 self.load_struct()
#             return self._tif

#         @tif.setter
#         def tif(self, value):
#             self._tif = value

#         def load_struct(self):
#             tif = get_named_type(self.name)
#             if tif.is_struct() or tif.is_union():
#                 self.tif = tif
#             self.tif = None
        
#         def create_struct(self, is_union):
#             self.load_struct()
#             if self.tif is None:
#                 idc.add_struc(-1, self.name, is_union)

#         def has_member_at(self, offset):
#             # type: (int) -> bool
#             return idc.get_member_id(self.tif.get_tid(), offset) != idc.BADADDR

#         def add_member(self, field_name, offset, field_type, is_baseclass = False, is_vtable = False, size = None):
#             ft = get_tinfo_from_type(field_type)
#             udm = create_udm(field_name, offset, ft)
#             if is_baseclass:
#                 udm.set_baseclass(True)
#             if size is not None:
#                 udm.size = size
#             if is_vtable:
#                 udm.set_vftable(True)
#             return self.tif.add_udm(udm)
        
#         def add_vfunc(self, virt_func):
#             offset = virt_func.offset
#             field_name = virt_func.name
            
#             if virt_func.return_type is None or virt_func.parameters is None:
#                 return
            
#             ftd = ida_typeinf.func_type_data_t()
#             ftd.cc = ida_typeinf.CM_CC_FASTCALL
#             ftd.rettype = get_tinfo_from_type(virt_func.return_type)

#             for param in virt_func.parameters:
#                 fa = ida_typeinf.funcarg_t()
#                 fa.name = param.name
#                 fa.type = get_tinfo_from_type(param.type)
#                 ftd.add_unique(fa)
            
#             fti = ida_typeinf.tinfo_t()
#             fti.create_func(ftd)
#             fti = idaapi.make_pointer(fti)

#             self.tif.add_udm(create_udm(field_name, offset, fti))

#         @property
#         def size(self):
#             return int(idc.get_struc_size(self.tif.get_tid())) / 8

#         def pad_to(self, offset, fullpad):
#             while offset > self.size:
#                 prev_size = self.size
#                 if fullpad:
#                     typ, size = get_padding_size(prev_size)
#                     if size > offset - prev_size:
#                         typ, size = get_padding_size(offset-prev_size, prev_size)
#                 else:
#                     typ, size = ("_BYTE", offset-prev_size)
#                 self.add_member("field_{0:X}".format(self.size), self.size, typ, size=size)

#         def delete_members(self):
#             pass