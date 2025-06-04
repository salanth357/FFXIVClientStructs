# @category __UserScripts
# @menupath Tools.Scripts.ffxiv_structimport
# @runtime Jython

from yaml import load
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

import os
from abc import abstractmethod
from time import time


class DefinedBase:
    def __init__(self, name, type, namespace):
        # type: (str, str, str) -> None
        self.name = name
        self.type = type
        self.namespace = namespace


class DefinedEnum(DefinedBase, object):
    def __init__(self, name, type, underlying, namespace, values):
        # type: (str, str, str, str, dict[str, int]) -> None
        super(DefinedEnum, self).__init__(name, type, namespace)
        self.name = name
        self.type = type
        self.values = values
        self.underlying = underlying


class DefinedFuncParam:
    def __init__(self, name, type):
        # type: (str, str) -> None
        self.name = name
        self.type = type


class DefinedVFunc:
    def __init__(self, name, return_type, offset, parameters):
        # type: (str, str, int, list[DefinedFuncParam]) -> None
        self.name = name
        self.return_type = return_type
        self.offset = offset
        self.parameters = parameters


class DefinedMemFunc:
    def __init__(self, signature, return_type, parameters, name):
        # type: (str, str, list[DefinedFuncParam], str) -> None
        self.signature = signature
        self.return_type = return_type
        self.parameters = parameters
        self.name = name


class DefinedField(DefinedFuncParam, object):
    def __init__(self, name, type, offset, base):
        # type: (str, str, int, bool) -> None
        super(DefinedField, self).__init__(name, type)
        self.offset = offset
        self.base = base


class DefinedFuncField(DefinedField, object):
    def __init__(self, name, type, offset, base, return_type, params):
        # type: (str, str, int, bool, str | None, list[DefinedFuncParam] | None) -> None
        super(DefinedFuncField, self).__init__(name, type, offset, base)
        self.return_type = return_type
        self.parameters = params

class DefinedStaticMember:
    def __init__(self, signature, relative_offsets, return_type, is_pointer):
        # type: (str, list[int], str, bool) -> None
        self.signature = signature
        self.relative_offsets = relative_offsets
        self.return_type = return_type
        self.is_pointer = is_pointer

class DefinedFixedField(DefinedField, object):
    def __init__(self, name, type, offset, base, size):
        # type: (str, str, int, bool, str | None) -> None
        super(DefinedFixedField, self).__init__(name, type, offset, base)
        self.size = size


class DefinedStruct(DefinedBase, object):
    def __init__(
        self,
        name,
        type,
        namespace,
        fields,
        size,
        virtual_functions,
        member_functions,
        union,
        static_member_functions,
        static_members
    ):
        # type: (str, str, str, list[DefinedField], int | None, list[DefinedVFunc] | None, list[DefinedMemFunc], str, list[DefinedMemFunc] | None, list[DefinedStaticMember] | None) -> None
        super(DefinedStruct, self).__init__(name, type, namespace)
        self.fields = fields
        self.size = size
        self.virtual_functions = virtual_functions
        self.member_functions = member_functions
        self.union = bool(union)
        self.static_member_functions = static_member_functions
        self.static_members = static_members


class DefinedExport:
    def __init__(self, enums, structs):
        # type: (list[DefinedEnum], list[DefinedStruct]) -> None
        self.enums = enums
        self.structs = structs


class BaseApi:
    @abstractmethod
    def create_enum(self, enum):
        # type: (DefinedEnum) -> None
        """
        Create an enum in the database.
        """

    @abstractmethod
    def delete_enum(self, enum):
        # type: (DefinedEnum) -> None
        """
        Delete an enum in the database.
        """

    @abstractmethod
    def delete_struct(self, struct):
        # type: (DefinedStruct) -> None
        """
        Delete a struct in the database.
        """

    @abstractmethod
    def create_struct(self, struct):
        # type: (DefinedStruct) -> None
        """
        Create a struct in the database.
        """

    @abstractmethod
    def create_struct_members(self, struct):
        # type: (DefinedStruct) -> None
        """
        Create members for a struct in the database.
        """

    @abstractmethod
    def create_vtable(self, struct):
        # type: (DefinedStruct) -> None
        """
        Create a vtable in the database.
        """

    @abstractmethod
    def create_union(self, struct):
        # type: (DefinedStruct) -> None
        """
        Create a union in the database.
        """

    @abstractmethod
    def update_member_func(self, member_func, struct):
        # type: (DefinedMemFunc, DefinedStruct) -> None
        """
        Updates a member function in the database.
        """

    @abstractmethod
    def update_virt_func(self, virt_func, struct):
        # type: (DefinedVFunc, DefinedStruct) -> None
        """
        Updates a virtual function in the database.
        """
        
    @abstractmethod
    def update_static_member(self, static_member, struct):
        # type: (DefinedStaticMember, DefinedStruct) -> None
        """
        Updates a static member in the database.
        """
    
    @abstractmethod
    def should_update_member_func(self):
        # type: () -> bool
        """
        Returns if the member function types should be updated.
        """

    @abstractmethod
    def should_update_virt_func(self):
        # type: () -> bool
        """
        Returns if the virtual function types should be updated.
        """

    @property
    @abstractmethod
    def get_file_path(self):
        """
        Retrieve the file path of the yaml file.
        """

    def get_yaml(self):
        # type: () -> DefinedExport
        dic = load(open(self.get_file_path), Loader=Loader) # type: dict[str, dict[str, list[dict[str, str | int | list[dict[str, str | int]]]]]]
        enums = []
        structs = []
        for enum in dic["enums"]:
            enums.append(
                DefinedEnum(
                    enum["name"],
                    enum["type"],
                    enum["underlying"],
                    enum["namespace"],
                    enum["values"],
                )
            )
        for struct in dic["structs"]:
            fields = []
            virtual_functions = None
            member_functions = []
            static_member_functions = None
            static_members = None
            for field in struct["fields"]:
                base = field["base"] if "base" in field else False
                if "size" in field:
                    fields.append(
                        DefinedFixedField(
                            field["name"],
                            field["type"],
                            field["offset"],
                            base,
                            field["size"],
                        )
                    )
                elif "return_type" in field:
                    parameters = []
                    for param in field["parameters"]:
                        parameters.append(
                            DefinedFuncParam(param["name"], param["type"])
                        )
                    fields.append(
                        DefinedFuncField(
                            field["name"],
                            field["type"],
                            field["offset"],
                            base,
                            field["return_type"],
                            parameters,
                        )
                    )
                else:
                    fields.append(
                        DefinedField(
                            field["name"], field["type"], field["offset"], base
                        )
                    )
            if "virtual_functions" in struct:
                virtual_functions = []
                for vfunc in struct["virtual_functions"]:
                    parameters = (
                        [
                            DefinedFuncParam(param["name"], param["type"])
                            for param in vfunc["parameters"]
                        ]
                        if "parameters" in vfunc
                        else None
                    )
                    virtual_functions.append(
                        DefinedVFunc(
                            vfunc["name"],
                            vfunc["return_type"] if "return_type" in vfunc else None,
                            vfunc["offset"],
                            parameters,
                        )
                    )
            for memfunc in struct["member_functions"]:
                parameters = []
                for param in memfunc["parameters"]:
                    parameters.append(DefinedFuncParam(param["name"], param["type"]))
                member_functions.append(
                    DefinedMemFunc(
                        memfunc["signature"],
                        memfunc["return_type"],
                        parameters,
                        memfunc["name"],
                    )
                )
            if "static_member_functions" in struct:
                static_member_functions = []
                for smemfunc in struct["static_member_functions"]:
                    parameters = []
                    for param in smemfunc["parameters"]:
                        parameters.append(
                            DefinedFuncParam(param["name"], param["type"])
                        )
                    static_member_functions.append(
                        DefinedMemFunc(
                            smemfunc["signature"],
                            smemfunc["return_type"],
                            parameters,
                            smemfunc["name"],
                        )
                    )
            if "static_members" in struct:
                static_members = []
                for sm in struct["static_members"]:
                    static_members.append(
                        DefinedStaticMember(sm["signature"], sm["relative_follow_offsets"], sm["return_type"], sm["is_pointer"] if "is_pointer" in sm else False)
                    )
            if "size" in struct:
                structs.append(
                    DefinedStruct(
                        struct["name"],
                        struct["type"],
                        struct["namespace"],
                        fields,
                        struct["size"],
                        virtual_functions,
                        member_functions,
                        struct["union"],
                        static_member_functions,
                        static_members
                    )
                )
            else:
                structs.append(
                    DefinedStruct(
                        struct["name"],
                        struct["type"],
                        struct["namespace"],
                        fields,
                        None,
                        virtual_functions,
                        member_functions,
                        struct["union"],
                        static_member_functions,
                        static_members
                    )
                )
        return DefinedExport(enums, structs)


api = None

if api is None:
    class IDAVersionException(Exception):
        pass
    try:
        import idaapi
        # if idaapi.IDA_SDK_VERSION < 900:
        #     raise IDAVersionException
        import idc
        import ida_bytes
        import ida_search
        import ida_typeinf
        import ida_funcs
        import ida_name
        import ida_kernwin
        import ida_helpers
        idaapi.require('ida_helpers')
    except ImportError:
        print("Warning: Unable to load IDA")
    except IDAVersionException:
        pass
    else:
        # noinspection PyUnresolvedReferences
        class Ida9Api(BaseApi):
            def __init__(self, full_padding):
                # type: (bool) -> None
                self.full_padding = full_padding

            def is_signed(self, type):
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

            def get_size_from_ida_type(self, type):
                # type: (str) -> int
                if (
                    type == "unsigned __int8"
                    or type == "__int8"
                    or type == "bool"
                    or type == "char"
                    or type == "unsigned char"
                    or type == "byte"
                ):
                    return 1
                elif type == "unsigned __int16" or type == "__int16" or type == "wchar_t":
                    return 2
                elif (
                    type == "unsigned __int32"
                    or type == "__int32"
                    or type == "int"
                    or type == "unsigned int"
                    or type == "_DWORD"
                    or type == "float"
                ):
                    return 4
                elif (
                    type == "unsigned __int64"
                    or type == "__int64"
                    or type == "__fastcall"
                    or type.endswith("*")
                    or type == "double"
                ):
                    return 8
                elif idc.get_struc_id(type) == idaapi.BADADDR:
                    return idc.get_enum_width(idc.get_enum(type))
                else:
                    return idc.get_struc_size(idc.get_struc_id(type))

            def get_dword(self, ea):
                return ida_bytes.get_original_dword(ea)

            def delete_enum_members(self, enum):
                # type: (DefinedEnum) -> None
                ida_helpers.IdaEnum(enum.type).delete_members()

            @property
            def get_file_path(self):
                return os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "ffxiv_structs.yml"
                )

            def create_enum(self, enum):
                # type: (DefinedEnum) -> None
                fullname = enum.type
                e = ida_helpers.IdaEnum(enum.type)
                e.create_enum(enum.underlying)
                for value in enum.values:
                    e.add_member(value, enum.values[value])

            def delete_enum(self, enum):
                # type: (DefinedEnum) -> None
                self.delete_enum_members(enum)

            def delete_struct(self, struct):
                # type: (DefinedStruct) -> None
                idaapi.begin_type_updating(idaapi.UTP_STRUCT)
                fullname = ida_helpers.clean_struct_name(struct.type)
                ida_helpers.IdaStruct(fullname).delete()
                ida_helpers.IdaStruct(fullname+"_vtbl").delete()
                idaapi.end_type_updating(idaapi.UTP_STRUCT)

            def create_struct(self, struct):
                # type: (DefinedStruct) -> None
                
                fullname = ida_helpers.clean_struct_name(struct.type)
                s = ida_helpers.IdaStruct(fullname)
                s.create_struct(struct.union)
                if struct.size is not None:
                    s.tif.set_fixed_struct()
                    s.tif.set_struct_size(struct.size)

                if struct.virtual_functions:
                    ida_helpers.IdaStruct(fullname+"_vtbl").create_struct(0)

            def create_struct_members(self, struct):
                # type: (DefinedStruct) -> None
                idaapi.begin_type_updating(idaapi.UTP_STRUCT)
                fullname = ida_helpers.clean_struct_name(struct.type)

                s = ida_helpers.IdaStruct(fullname)
                
                if struct.virtual_functions != None and (
                    struct.fields == [] or struct.fields[0].offset > 0
                ):
                    s.add_member(
                        "__vftable",
                        0,
                        fullname+"_vtbl*" if struct.virtual_functions else "void**",
                        is_vtable = True,
                    )

                contiguous_fields = True

                for field in struct.fields:
                    offset = field.offset

                    prev_size = s.size
                    if offset > prev_size:
                        contiguous_fields = False
                        s.pad_to(offset, self.full_padding)

                    field_is_base = field.base and contiguous_fields
                    field_name = (
                        field.name if not field_is_base else "baseclass_{0:X}".format(offset)
                    )
                    field_type = field.type

                    if field_type == "__fastcall":
                        field_type = "{0}(__fastcall* {1})({2})".format(
                            field.return_type,
                            field_name,
                            ','.join(["{0} {1}".format(ida_helpers.clean_struct_name(param.type), param.name) for param in field.parameters])
                        )
                    elif ida_helpers.get_idc_type_from_ida_type(
                        ida_helpers.clean_struct_name(field_type)) == ida_bytes.stru_flag():
                        field_type = ida_helpers.clean_struct_name(field_type)

                    size = getattr(field, "size", 0)
                    s.add_member(field_name, offset, field_type, is_baseclass = field_is_base, size = size)

                if struct.size is not None and struct.size != 0 and struct.size > s.size:
                    s.pad_to(s.size, self.full_padding)
                idaapi.end_type_updating(idaapi.UTP_STRUCT)

            def create_vtable(self, struct):
                # type: (DefinedStruct) -> None
                fullname = ida_helpers.clean_struct_name(struct.type)
                s = ida_helpers.IdaStruct(fullname + "_vtbl")

                for virt_func in struct.virtual_functions:
                    s.add_vfunc(virt_func)

                for i in range(s.size):
                    if not s.has_member_at(i*8):
                        s.add_member("vf{0}".format(i), i*8, "__int64")

            def create_union(self, struct):
                # type: (DefinedStruct) -> None
                pass

            def update_member_func(self, member_func, struct):
                # type: (DefinedMemFunc, DefinedStruct) -> None
                func_name = "{0}.{1}".format(
                    struct.type, member_func.name
                )
                ea = ida_helpers.get_func_ea_by_name(func_name)
                if ea == idc.BADADDR:
                    ea = ida_helpers.get_func_ea_by_sig(member_func.signature)
                if ea == idc.BADADDR:
                    print(
                        "Error: {0} not found bad sig? {1}".format(
                            func_name, member_func.signature
                        )
                    )
                    return
                if ida_funcs.get_func_name(ea) == "sub_{0:X}".format(ea):
                    idc.set_name(ea, func_name)
                tif = ida_typeinf.tinfo_t()
                ida_typeinf.guess_tinfo(tif, ea)
                func_data = ida_typeinf.func_type_data_t()
                tif.get_func_details(func_data)
                func_data.clear()
                func_data.cc = ida_typeinf.CM_CC_FASTCALL
                func_data.rettype = ida_helpers.get_tinfo_from_type(member_func.return_type)
                for param in member_func.parameters:
                    arg = ida_typeinf.funcarg_t()
                    arg.type = ida_helpers.get_tinfo_from_type(param.type)
                    arg.name = param.name
                    func_data.push_back(arg)
                tif.create_func(func_data)
                ida_typeinf.apply_tinfo(ea, tif, ida_typeinf.TINFO_DEFINITE)

            def update_virt_func(self, virt_func, struct):
                # type: (DefinedVFunc, DefinedStruct) -> None
                func_name = "{0}.{1}".format(
                    ida_helpers.clean_struct_name(struct.type), virt_func.name
                )
                ea = ida_helpers.get_func_ea_by_name(func_name)
                if ea == idc.BADADDR:
                    print("Warn: {0} not found - likely using base?".format(func_name))
                    return
                tif = ida_typeinf.tinfo_t()
                ida_typeinf.guess_tinfo(tif, ea)
                func_data = ida_typeinf.func_type_data_t()
                tif.get_func_details(func_data)
                func_data.clear()
                func_data.cc = ida_typeinf.CM_CC_FASTCALL
                func_data.rettype = ida_helpers.get_tinfo_from_type(virt_func.return_type)
                for param in virt_func.parameters:
                    arg = ida_typeinf.funcarg_t()
                    arg.type = ida_helpers.get_tinfo_from_type(param.type)
                    arg.name = param.name
                    func_data.push_back(arg)
                tif.create_func(func_data)
                ida_typeinf.apply_tinfo(ea, tif, ida_typeinf.TINFO_DEFINITE)
            
            def update_static_member(self, static_member, struct):
                # type: (DefinedStaticMember, DefinedStruct) -> None
                ea = ida_helpers.search_binary(0, static_member.signature, flag=ida_search.SEARCH_DOWN)
                if ea == idc.BADADDR:
                    print("Error: {0} not found something is wrong".format(static_member.signature))
                    return
                for follows in static_member.relative_offsets:
                    ea = ea + follows
                    ea = ea + 4 + self.get_dword(ea)
                tif = ida_typeinf.tinfo_t()
                ida_typeinf.guess_tinfo(tif, ea)
                return_type = static_member.return_type
                if static_member.is_pointer:
                    return_type = return_type + "*"
                ida_typeinf.apply_tinfo(ea, ida_helpers.get_tinfo_from_type(return_type), ida_typeinf.TINFO_DEFINITE)
                if static_member.is_pointer:
                    ida_name.set_name(ea, "g_{0}_{1}".format(ida_helpers.clean_struct_name(struct.type), "PtrInstance"))
                else:
                    ida_name.set_name(ea, "g_{0}_{1}".format(ida_helpers.clean_struct_name(struct.type), "Instance"))

            def should_update_member_func(self):
                return (
                    ida_kernwin.ask_yn(
                        ida_kernwin.ASKBTN_YES, "Update member function types?"
                    )
                    == ida_kernwin.ASKBTN_YES
                )

            def should_update_virt_func(self):
                return (
                    ida_kernwin.ask_yn(
                        ida_kernwin.ASKBTN_YES, "Update virtual function types?"
                    )
                    == ida_kernwin.ASKBTN_YES
                )

        full_padding = (
            ida_kernwin.ask_buttons(
                "Full Padding",
                "Array Padding",
                "",
                ida_kernwin.ASKBTN_YES,
                "HIDECANCEL\nWhat padding style to use?\n\nFull Padding: Adds padding based on allignment of 1,2,4,8\nArray Padding: Adds padding based on the size between fields with byte arrays\n\nFull Padding will take longer to add padding between fields but is recommended for quick struct modifications.",
            )
            == ida_kernwin.ASKBTN_YES
        )
        api = Ida9Api(full_padding)

if api is None:
    raise Exception("Unable to load API (supported: IDA, Ghidra, Binary Ninja)")

start_time = time()


def get_time():
    val = round(time() - start_time, 6).__str__()
    while val.split(".")[-1].__len__() < 6:
        val += "0"
    return val


def run():
    print("{0} Loading yaml".format(get_time()))
    yaml = api.get_yaml()

    print("{0} Deleting old structs".format(get_time()))
    for struct in yaml.structs[::-1]:
        api.delete_struct(struct)

    print("{0} Deleting old enums and creating new ones".format(get_time()))
    for enum in yaml.enums:
        api.delete_enum(enum)
        api.create_enum(enum)

    print("{0} Creating new structs".format(get_time()))
    for struct in yaml.structs:
        api.create_struct(struct)

    print("{0} Creating members for structs".format(get_time()))
    for struct in yaml.structs:
        api.create_struct_members(struct)

    print("{0} Creating vtables for structs".format(get_time()))
    for struct in yaml.structs:
        if struct.virtual_functions:
            api.create_vtable(struct)

    print("{0} Mapping unions/vtables for structs".format(get_time()))
    for struct in yaml.structs:
        api.create_union(struct)

    if api.should_update_virt_func():
        for struct in yaml.structs:
            if struct.virtual_functions:
                print(
                    "{0} Updating virtual functions for {1}".format(
                        get_time(), struct.type
                    )
                )
                for virt_func in struct.virtual_functions:
                    if virt_func.return_type != None and virt_func.parameters != None:
                        api.update_virt_func(virt_func, struct)

    if api.should_update_member_func():
        for struct in yaml.structs:
            if struct.member_functions != []:
                print(
                    "{0} Updating member functions for {1}".format(
                        get_time(), struct.type
                    )
                )
                for member_func in struct.member_functions:
                    api.update_member_func(member_func, struct)
            
            if struct.static_member_functions:
                print(
                    "{0} Updating static member functions for {1}".format(
                        get_time(), struct.type
                    )
                )
                for member_func in struct.static_member_functions:
                    api.update_member_func(member_func, struct)
            
            if struct.static_members:
                print(
                    "{0} Updating static members for {1}".format(
                        get_time(), struct.type
                    )
                )
                for member in struct.static_members:
                    api.update_static_member(member, struct)


run()
