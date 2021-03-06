# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: laiteviestit.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='laiteviestit.proto',
  package='fi.metatavu.jouko.api.device',
  syntax='proto2',
  serialized_pb=_b('\n\x12laiteviestit.proto\x12\x1c\x66i.metatavu.jouko.api.device\"\x8c\x01\n\x06Katkot\x12:\n\x06katkot\x18\x01 \x03(\x0b\x32*.fi.metatavu.jouko.api.device.Katkot.Katko\x1a\x46\n\x05Katko\x12\x0f\n\x07katkoID\x18\x01 \x02(\x03\x12\x0f\n\x07laiteID\x18\x02 \x02(\x03\x12\x0c\n\x04\x61lku\x18\x03 \x02(\x03\x12\r\n\x05loppu\x18\x04 \x02(\x03\"w\n\x0bKatkonestot\x12I\n\x0bkatkonestot\x18\x01 \x03(\x0b\x32\x34.fi.metatavu.jouko.api.device.Katkonestot.Katkonesto\x1a\x1d\n\nKatkonesto\x12\x0f\n\x07katkoID\x18\x01 \x02(\x03\"$\n\x12\x41ikasynkLaitteelle\x12\x0e\n\x06\x65rotus\x18\x01 \x02(\x03\"$\n\x0cVersioKysely\x12\x14\n\x0cversioKysely\x18\x01 \x02(\x08\"!\n\rSbUpdateStart\x12\x10\n\x08numFiles\x18\x01 \x02(\x05\")\n\x0cSbUpdatePart\x12\x0b\n\x03num\x18\x01 \x02(\x03\x12\x0c\n\x04part\x18\x02 \x02(\t\"[\n\x0cSbUpdateStop\x12\x11\n\tsplitSize\x18\x01 \x02(\x03\x12\x10\n\x08numFiles\x18\x02 \x02(\x05\x12\x10\n\x08\x66ileName\x18\x03 \x02(\t\x12\x14\n\x0cversioNumero\x18\x04 \x02(\x05\"X\n\x0eSbUpdateFinish\x12\x10\n\x08updateId\x18\x01 \x02(\x05\x12\x10\n\x08\x66ileName\x18\x02 \x02(\t\x12\x10\n\x08numParts\x18\x03 \x02(\x05\x12\x10\n\x08\x63heckSum\x18\x04 \x01(\x05\"\x8f\x01\n\x0fSbUpdateInstall\x12\x10\n\x08updateId\x18\x01 \x03(\x05\x12N\n\x0binstallType\x18\x02 \x02(\x0e\x32\x39.fi.metatavu.jouko.api.device.SbUpdateInstall.InstallType\"\x1a\n\x0bInstallType\x12\x0b\n\x07RESTART\x10\x00\"q\n\nMittaukset\x12\x12\n\nkeskiarvot\x18\x01 \x03(\x05\x12\x19\n\x11pituusMinuutteina\x18\x02 \x01(\x05\x12\x0c\n\x04\x61ika\x18\x03 \x02(\x03\x12\x0f\n\x07laiteID\x18\x04 \x02(\x03\x12\x15\n\rreleOhjaukset\x18\x05 \x02(\x05\"\x1f\n\rVersioVastaus\x12\x0e\n\x06versio\x18\x01 \x02(\x03\"4\n\x12\x41ikasynkLaitteelta\x12\x11\n\tlaiteaika\x18\x01 \x02(\x03\x12\x0b\n\x03syy\x18\x02 \x01(\x05\"\x8a\x05\n\x10ViestiLaitteelle\x12\x36\n\x06katkot\x18\x01 \x01(\x0b\x32$.fi.metatavu.jouko.api.device.KatkotH\x00\x12@\n\x0bkatkonestot\x18\x02 \x01(\x0b\x32).fi.metatavu.jouko.api.device.KatkonestotH\x00\x12N\n\x12\x61ikasynkLaitteelle\x18\x03 \x01(\x0b\x32\x30.fi.metatavu.jouko.api.device.AikasynkLaitteelleH\x00\x12\x42\n\x0csbUpdatePart\x18\x04 \x01(\x0b\x32*.fi.metatavu.jouko.api.device.SbUpdatePartH\x00\x12\x46\n\x0esbUpdateFinish\x18\x05 \x01(\x0b\x32,.fi.metatavu.jouko.api.device.SbUpdateFinishH\x00\x12H\n\x0fsbUpdateInstall\x18\x06 \x01(\x0b\x32-.fi.metatavu.jouko.api.device.SbUpdateInstallH\x00\x12\x42\n\x0cversioKysely\x18\x07 \x01(\x0b\x32*.fi.metatavu.jouko.api.device.VersioKyselyH\x00\x12\x44\n\rsbUpdateStart\x18\x08 \x01(\x0b\x32+.fi.metatavu.jouko.api.device.SbUpdateStartH\x00\x12\x42\n\x0csbUpdateStop\x18\t \x01(\x0b\x32*.fi.metatavu.jouko.api.device.SbUpdateStopH\x00\x42\x08\n\x06viesti\"\xf2\x01\n\x10ViestiLaitteelta\x12>\n\nmittaukset\x18\x01 \x01(\x0b\x32(.fi.metatavu.jouko.api.device.MittauksetH\x00\x12N\n\x12\x61ikasynkLaitteelta\x18\x02 \x01(\x0b\x32\x30.fi.metatavu.jouko.api.device.AikasynkLaitteeltaH\x00\x12\x44\n\rversioVastaus\x18\x03 \x01(\x0b\x32+.fi.metatavu.jouko.api.device.VersioVastausH\x00\x42\x08\n\x06viesti')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_SBUPDATEINSTALL_INSTALLTYPE = _descriptor.EnumDescriptor(
  name='InstallType',
  full_name='fi.metatavu.jouko.api.device.SbUpdateInstall.InstallType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='RESTART', index=0, number=0,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=771,
  serialized_end=797,
)
_sym_db.RegisterEnumDescriptor(_SBUPDATEINSTALL_INSTALLTYPE)


_KATKOT_KATKO = _descriptor.Descriptor(
  name='Katko',
  full_name='fi.metatavu.jouko.api.device.Katkot.Katko',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='katkoID', full_name='fi.metatavu.jouko.api.device.Katkot.Katko.katkoID', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='laiteID', full_name='fi.metatavu.jouko.api.device.Katkot.Katko.laiteID', index=1,
      number=2, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='alku', full_name='fi.metatavu.jouko.api.device.Katkot.Katko.alku', index=2,
      number=3, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='loppu', full_name='fi.metatavu.jouko.api.device.Katkot.Katko.loppu', index=3,
      number=4, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=123,
  serialized_end=193,
)

_KATKOT = _descriptor.Descriptor(
  name='Katkot',
  full_name='fi.metatavu.jouko.api.device.Katkot',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='katkot', full_name='fi.metatavu.jouko.api.device.Katkot.katkot', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_KATKOT_KATKO, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=53,
  serialized_end=193,
)


_KATKONESTOT_KATKONESTO = _descriptor.Descriptor(
  name='Katkonesto',
  full_name='fi.metatavu.jouko.api.device.Katkonestot.Katkonesto',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='katkoID', full_name='fi.metatavu.jouko.api.device.Katkonestot.Katkonesto.katkoID', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=285,
  serialized_end=314,
)

_KATKONESTOT = _descriptor.Descriptor(
  name='Katkonestot',
  full_name='fi.metatavu.jouko.api.device.Katkonestot',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='katkonestot', full_name='fi.metatavu.jouko.api.device.Katkonestot.katkonestot', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_KATKONESTOT_KATKONESTO, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=195,
  serialized_end=314,
)


_AIKASYNKLAITTEELLE = _descriptor.Descriptor(
  name='AikasynkLaitteelle',
  full_name='fi.metatavu.jouko.api.device.AikasynkLaitteelle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='erotus', full_name='fi.metatavu.jouko.api.device.AikasynkLaitteelle.erotus', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=316,
  serialized_end=352,
)


_VERSIOKYSELY = _descriptor.Descriptor(
  name='VersioKysely',
  full_name='fi.metatavu.jouko.api.device.VersioKysely',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='versioKysely', full_name='fi.metatavu.jouko.api.device.VersioKysely.versioKysely', index=0,
      number=1, type=8, cpp_type=7, label=2,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=354,
  serialized_end=390,
)


_SBUPDATESTART = _descriptor.Descriptor(
  name='SbUpdateStart',
  full_name='fi.metatavu.jouko.api.device.SbUpdateStart',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='numFiles', full_name='fi.metatavu.jouko.api.device.SbUpdateStart.numFiles', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=392,
  serialized_end=425,
)


_SBUPDATEPART = _descriptor.Descriptor(
  name='SbUpdatePart',
  full_name='fi.metatavu.jouko.api.device.SbUpdatePart',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='num', full_name='fi.metatavu.jouko.api.device.SbUpdatePart.num', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='part', full_name='fi.metatavu.jouko.api.device.SbUpdatePart.part', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=427,
  serialized_end=468,
)


_SBUPDATESTOP = _descriptor.Descriptor(
  name='SbUpdateStop',
  full_name='fi.metatavu.jouko.api.device.SbUpdateStop',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='splitSize', full_name='fi.metatavu.jouko.api.device.SbUpdateStop.splitSize', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='numFiles', full_name='fi.metatavu.jouko.api.device.SbUpdateStop.numFiles', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='fileName', full_name='fi.metatavu.jouko.api.device.SbUpdateStop.fileName', index=2,
      number=3, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='versioNumero', full_name='fi.metatavu.jouko.api.device.SbUpdateStop.versioNumero', index=3,
      number=4, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=470,
  serialized_end=561,
)


_SBUPDATEFINISH = _descriptor.Descriptor(
  name='SbUpdateFinish',
  full_name='fi.metatavu.jouko.api.device.SbUpdateFinish',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='updateId', full_name='fi.metatavu.jouko.api.device.SbUpdateFinish.updateId', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='fileName', full_name='fi.metatavu.jouko.api.device.SbUpdateFinish.fileName', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='numParts', full_name='fi.metatavu.jouko.api.device.SbUpdateFinish.numParts', index=2,
      number=3, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='checkSum', full_name='fi.metatavu.jouko.api.device.SbUpdateFinish.checkSum', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=563,
  serialized_end=651,
)


_SBUPDATEINSTALL = _descriptor.Descriptor(
  name='SbUpdateInstall',
  full_name='fi.metatavu.jouko.api.device.SbUpdateInstall',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='updateId', full_name='fi.metatavu.jouko.api.device.SbUpdateInstall.updateId', index=0,
      number=1, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='installType', full_name='fi.metatavu.jouko.api.device.SbUpdateInstall.installType', index=1,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _SBUPDATEINSTALL_INSTALLTYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=654,
  serialized_end=797,
)


_MITTAUKSET = _descriptor.Descriptor(
  name='Mittaukset',
  full_name='fi.metatavu.jouko.api.device.Mittaukset',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='keskiarvot', full_name='fi.metatavu.jouko.api.device.Mittaukset.keskiarvot', index=0,
      number=1, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='pituusMinuutteina', full_name='fi.metatavu.jouko.api.device.Mittaukset.pituusMinuutteina', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='aika', full_name='fi.metatavu.jouko.api.device.Mittaukset.aika', index=2,
      number=3, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='laiteID', full_name='fi.metatavu.jouko.api.device.Mittaukset.laiteID', index=3,
      number=4, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='releOhjaukset', full_name='fi.metatavu.jouko.api.device.Mittaukset.releOhjaukset', index=4,
      number=5, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=799,
  serialized_end=912,
)


_VERSIOVASTAUS = _descriptor.Descriptor(
  name='VersioVastaus',
  full_name='fi.metatavu.jouko.api.device.VersioVastaus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='versio', full_name='fi.metatavu.jouko.api.device.VersioVastaus.versio', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=914,
  serialized_end=945,
)


_AIKASYNKLAITTEELTA = _descriptor.Descriptor(
  name='AikasynkLaitteelta',
  full_name='fi.metatavu.jouko.api.device.AikasynkLaitteelta',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='laiteaika', full_name='fi.metatavu.jouko.api.device.AikasynkLaitteelta.laiteaika', index=0,
      number=1, type=3, cpp_type=2, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='syy', full_name='fi.metatavu.jouko.api.device.AikasynkLaitteelta.syy', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=947,
  serialized_end=999,
)


_VIESTILAITTEELLE = _descriptor.Descriptor(
  name='ViestiLaitteelle',
  full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='katkot', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.katkot', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='katkonestot', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.katkonestot', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='aikasynkLaitteelle', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.aikasynkLaitteelle', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sbUpdatePart', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.sbUpdatePart', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sbUpdateFinish', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.sbUpdateFinish', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sbUpdateInstall', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.sbUpdateInstall', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='versioKysely', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.versioKysely', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sbUpdateStart', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.sbUpdateStart', index=7,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sbUpdateStop', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.sbUpdateStop', index=8,
      number=9, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='viesti', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelle.viesti',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=1002,
  serialized_end=1652,
)


_VIESTILAITTEELTA = _descriptor.Descriptor(
  name='ViestiLaitteelta',
  full_name='fi.metatavu.jouko.api.device.ViestiLaitteelta',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='mittaukset', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelta.mittaukset', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='aikasynkLaitteelta', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelta.aikasynkLaitteelta', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='versioVastaus', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelta.versioVastaus', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='viesti', full_name='fi.metatavu.jouko.api.device.ViestiLaitteelta.viesti',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=1655,
  serialized_end=1897,
)

_KATKOT_KATKO.containing_type = _KATKOT
_KATKOT.fields_by_name['katkot'].message_type = _KATKOT_KATKO
_KATKONESTOT_KATKONESTO.containing_type = _KATKONESTOT
_KATKONESTOT.fields_by_name['katkonestot'].message_type = _KATKONESTOT_KATKONESTO
_SBUPDATEINSTALL.fields_by_name['installType'].enum_type = _SBUPDATEINSTALL_INSTALLTYPE
_SBUPDATEINSTALL_INSTALLTYPE.containing_type = _SBUPDATEINSTALL
_VIESTILAITTEELLE.fields_by_name['katkot'].message_type = _KATKOT
_VIESTILAITTEELLE.fields_by_name['katkonestot'].message_type = _KATKONESTOT
_VIESTILAITTEELLE.fields_by_name['aikasynkLaitteelle'].message_type = _AIKASYNKLAITTEELLE
_VIESTILAITTEELLE.fields_by_name['sbUpdatePart'].message_type = _SBUPDATEPART
_VIESTILAITTEELLE.fields_by_name['sbUpdateFinish'].message_type = _SBUPDATEFINISH
_VIESTILAITTEELLE.fields_by_name['sbUpdateInstall'].message_type = _SBUPDATEINSTALL
_VIESTILAITTEELLE.fields_by_name['versioKysely'].message_type = _VERSIOKYSELY
_VIESTILAITTEELLE.fields_by_name['sbUpdateStart'].message_type = _SBUPDATESTART
_VIESTILAITTEELLE.fields_by_name['sbUpdateStop'].message_type = _SBUPDATESTOP
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['katkot'])
_VIESTILAITTEELLE.fields_by_name['katkot'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['katkonestot'])
_VIESTILAITTEELLE.fields_by_name['katkonestot'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['aikasynkLaitteelle'])
_VIESTILAITTEELLE.fields_by_name['aikasynkLaitteelle'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['sbUpdatePart'])
_VIESTILAITTEELLE.fields_by_name['sbUpdatePart'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['sbUpdateFinish'])
_VIESTILAITTEELLE.fields_by_name['sbUpdateFinish'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['sbUpdateInstall'])
_VIESTILAITTEELLE.fields_by_name['sbUpdateInstall'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['versioKysely'])
_VIESTILAITTEELLE.fields_by_name['versioKysely'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['sbUpdateStart'])
_VIESTILAITTEELLE.fields_by_name['sbUpdateStart'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELLE.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELLE.fields_by_name['sbUpdateStop'])
_VIESTILAITTEELLE.fields_by_name['sbUpdateStop'].containing_oneof = _VIESTILAITTEELLE.oneofs_by_name['viesti']
_VIESTILAITTEELTA.fields_by_name['mittaukset'].message_type = _MITTAUKSET
_VIESTILAITTEELTA.fields_by_name['aikasynkLaitteelta'].message_type = _AIKASYNKLAITTEELTA
_VIESTILAITTEELTA.fields_by_name['versioVastaus'].message_type = _VERSIOVASTAUS
_VIESTILAITTEELTA.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELTA.fields_by_name['mittaukset'])
_VIESTILAITTEELTA.fields_by_name['mittaukset'].containing_oneof = _VIESTILAITTEELTA.oneofs_by_name['viesti']
_VIESTILAITTEELTA.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELTA.fields_by_name['aikasynkLaitteelta'])
_VIESTILAITTEELTA.fields_by_name['aikasynkLaitteelta'].containing_oneof = _VIESTILAITTEELTA.oneofs_by_name['viesti']
_VIESTILAITTEELTA.oneofs_by_name['viesti'].fields.append(
  _VIESTILAITTEELTA.fields_by_name['versioVastaus'])
_VIESTILAITTEELTA.fields_by_name['versioVastaus'].containing_oneof = _VIESTILAITTEELTA.oneofs_by_name['viesti']
DESCRIPTOR.message_types_by_name['Katkot'] = _KATKOT
DESCRIPTOR.message_types_by_name['Katkonestot'] = _KATKONESTOT
DESCRIPTOR.message_types_by_name['AikasynkLaitteelle'] = _AIKASYNKLAITTEELLE
DESCRIPTOR.message_types_by_name['VersioKysely'] = _VERSIOKYSELY
DESCRIPTOR.message_types_by_name['SbUpdateStart'] = _SBUPDATESTART
DESCRIPTOR.message_types_by_name['SbUpdatePart'] = _SBUPDATEPART
DESCRIPTOR.message_types_by_name['SbUpdateStop'] = _SBUPDATESTOP
DESCRIPTOR.message_types_by_name['SbUpdateFinish'] = _SBUPDATEFINISH
DESCRIPTOR.message_types_by_name['SbUpdateInstall'] = _SBUPDATEINSTALL
DESCRIPTOR.message_types_by_name['Mittaukset'] = _MITTAUKSET
DESCRIPTOR.message_types_by_name['VersioVastaus'] = _VERSIOVASTAUS
DESCRIPTOR.message_types_by_name['AikasynkLaitteelta'] = _AIKASYNKLAITTEELTA
DESCRIPTOR.message_types_by_name['ViestiLaitteelle'] = _VIESTILAITTEELLE
DESCRIPTOR.message_types_by_name['ViestiLaitteelta'] = _VIESTILAITTEELTA

Katkot = _reflection.GeneratedProtocolMessageType('Katkot', (_message.Message,), dict(

  Katko = _reflection.GeneratedProtocolMessageType('Katko', (_message.Message,), dict(
    DESCRIPTOR = _KATKOT_KATKO,
    __module__ = 'laiteviestit_pb2'
    # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.Katkot.Katko)
    ))
  ,
  DESCRIPTOR = _KATKOT,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.Katkot)
  ))
_sym_db.RegisterMessage(Katkot)
_sym_db.RegisterMessage(Katkot.Katko)

Katkonestot = _reflection.GeneratedProtocolMessageType('Katkonestot', (_message.Message,), dict(

  Katkonesto = _reflection.GeneratedProtocolMessageType('Katkonesto', (_message.Message,), dict(
    DESCRIPTOR = _KATKONESTOT_KATKONESTO,
    __module__ = 'laiteviestit_pb2'
    # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.Katkonestot.Katkonesto)
    ))
  ,
  DESCRIPTOR = _KATKONESTOT,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.Katkonestot)
  ))
_sym_db.RegisterMessage(Katkonestot)
_sym_db.RegisterMessage(Katkonestot.Katkonesto)

AikasynkLaitteelle = _reflection.GeneratedProtocolMessageType('AikasynkLaitteelle', (_message.Message,), dict(
  DESCRIPTOR = _AIKASYNKLAITTEELLE,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.AikasynkLaitteelle)
  ))
_sym_db.RegisterMessage(AikasynkLaitteelle)

VersioKysely = _reflection.GeneratedProtocolMessageType('VersioKysely', (_message.Message,), dict(
  DESCRIPTOR = _VERSIOKYSELY,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.VersioKysely)
  ))
_sym_db.RegisterMessage(VersioKysely)

SbUpdateStart = _reflection.GeneratedProtocolMessageType('SbUpdateStart', (_message.Message,), dict(
  DESCRIPTOR = _SBUPDATESTART,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.SbUpdateStart)
  ))
_sym_db.RegisterMessage(SbUpdateStart)

SbUpdatePart = _reflection.GeneratedProtocolMessageType('SbUpdatePart', (_message.Message,), dict(
  DESCRIPTOR = _SBUPDATEPART,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.SbUpdatePart)
  ))
_sym_db.RegisterMessage(SbUpdatePart)

SbUpdateStop = _reflection.GeneratedProtocolMessageType('SbUpdateStop', (_message.Message,), dict(
  DESCRIPTOR = _SBUPDATESTOP,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.SbUpdateStop)
  ))
_sym_db.RegisterMessage(SbUpdateStop)

SbUpdateFinish = _reflection.GeneratedProtocolMessageType('SbUpdateFinish', (_message.Message,), dict(
  DESCRIPTOR = _SBUPDATEFINISH,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.SbUpdateFinish)
  ))
_sym_db.RegisterMessage(SbUpdateFinish)

SbUpdateInstall = _reflection.GeneratedProtocolMessageType('SbUpdateInstall', (_message.Message,), dict(
  DESCRIPTOR = _SBUPDATEINSTALL,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.SbUpdateInstall)
  ))
_sym_db.RegisterMessage(SbUpdateInstall)

Mittaukset = _reflection.GeneratedProtocolMessageType('Mittaukset', (_message.Message,), dict(
  DESCRIPTOR = _MITTAUKSET,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.Mittaukset)
  ))
_sym_db.RegisterMessage(Mittaukset)

VersioVastaus = _reflection.GeneratedProtocolMessageType('VersioVastaus', (_message.Message,), dict(
  DESCRIPTOR = _VERSIOVASTAUS,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.VersioVastaus)
  ))
_sym_db.RegisterMessage(VersioVastaus)

AikasynkLaitteelta = _reflection.GeneratedProtocolMessageType('AikasynkLaitteelta', (_message.Message,), dict(
  DESCRIPTOR = _AIKASYNKLAITTEELTA,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.AikasynkLaitteelta)
  ))
_sym_db.RegisterMessage(AikasynkLaitteelta)

ViestiLaitteelle = _reflection.GeneratedProtocolMessageType('ViestiLaitteelle', (_message.Message,), dict(
  DESCRIPTOR = _VIESTILAITTEELLE,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.ViestiLaitteelle)
  ))
_sym_db.RegisterMessage(ViestiLaitteelle)

ViestiLaitteelta = _reflection.GeneratedProtocolMessageType('ViestiLaitteelta', (_message.Message,), dict(
  DESCRIPTOR = _VIESTILAITTEELTA,
  __module__ = 'laiteviestit_pb2'
  # @@protoc_insertion_point(class_scope:fi.metatavu.jouko.api.device.ViestiLaitteelta)
  ))
_sym_db.RegisterMessage(ViestiLaitteelta)


# @@protoc_insertion_point(module_scope)
