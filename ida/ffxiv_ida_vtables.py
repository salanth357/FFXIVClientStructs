import os
import ida_typeinf
import ida_helpers

from yaml import load
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

filepath = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data.yml"
)

dic = load(open(filepath), Loader=Loader) # type: dict[str, dict[str, dict[str, list[dict[str, int]]]]]

for name, cls in dic['classes'].items():
    if cls is None:
        continue
    vtbls = cls.get('vtbls', None)
    if vtbls is None:
        continue
    if len(vtbls) > 1:
        continue

    s = ida_helpers.IdaStruct(name)
    if s.tif is None:
        continue
    ida_typeinf.set_vftable_ea(s.tif.get_ordinal(), vtbls[0]['ea'])