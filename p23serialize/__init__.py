
from __future__ import print_function

import sys
from base64 import b64encode, b64decode
import re
import numpy as np
import json
#import msgpack


# Exception that should never be reachable in the code if the functions
# are used as intended.
class NeverHappens(Exception): pass


try:
    unicode
    # Note: in python2:  str == bytes
    str_mode = 'bytes'
except NameError:
    # In python3 unicode builtin is deprecated, i.e. not defined
    # "str" replaces it as the primary str type.
    str_mode = 'unicode'

if str_mode == 'bytes':  # typically python2

    str_types = (str, unicode)
    def force_str_type0(s):
        if isinstance(s, str_types[1]):
            return s.encode()
        return s
    def encode_str(s):
        if isinstance(s, bytes):
            return 'b' + s
        elif isinstance(s, unicode):
            return 'u' + s.encode('utf8')
        else:
            raise NeverHappens
    def decode_str(s):
        if isinstance(s, bytes):
            if s[:1] == 'b':
                return s[1:]
            elif s[:1] == 'u':
                return s[1:].decode('utf8')
            else:
                raise Exception('Bad string' + s)
        elif isinstance(s, unicode):
            if s[:1] == u'b':
                return s[1:].encode('latin1')
            elif s[:1] == u'u':
                return s[1:]
            else:
                raise Exception('Bad string' + s.encode())
        else:
            raise NeverHappens

elif str_mode == 'unicode':  # typically python3

    str_types = (str, bytes)
    def force_str_type0(s):
        if isinstance(s, str_types[1]):
            return s.decode()
        return s
    def encode_str(s):
        if isinstance(s, bytes):
            return 'b' + s.decode('latin1')
        elif isinstance(s, str):
            return 'u' + s
        else:
            raise NeverHappens
    def decode_str(s):
        if isinstance(s, bytes):
            if s[:1] == b'b':
                return s[1:]
            elif s[:1] == b'u':
                return s[1:].decode('utf8')
            else:
                raise Exception('Bad string' + s.decode('latin1'))
        elif isinstance(s, str):
            if s[:1] == 'b':
                return s[1:].encode('latin1')
            elif s[:1] == 'u':
                return s[1:]
            else:
                raise Exception('Bad string' + s.encode())
        else:
            raise NeverHappens

else:  # str_mode *cannot* be something else
    raise NeverHappens

# Update dictionary keys so that they are all of the native string type
def force_str_type0_keys(dct):
    for key in dct:
        key_fixed = force_str_type0(key)
        if not key_fixed in dct:
            dct[key_fixed] = dct[key]
            del dct[key]

'''
NOTES:

Encoder functions:
- One input parameter: object
- Two outputs:
  - Data for initial object reconstruction  (e.g. whether numpy ndarray is an object, or just array)
  - Data to complete the object reconstruction  (e.g. numpy shape, dtype, data_bytes)

Decoder functions:
- There are 2 decoder functions
  - Initial construction Decoder
    - Takes one parameter that has the data in
    - Bare minimum to create the object so we can have a consistent reference to it
    - Return the desired object
  - Final function that completes the object construction
    - First parameter is a copy of the object being worked on
      (None if object does not exist yet)
    - Second parameter is data needed to finalize this object.
    - Return the desired object. Must be the same object (by id(...)) if the
      first parameter was not None

'''


class Slot():
    def __init__(self, obj, idx):
        self.raw = obj
        self.encoded = None
        self.done = False
        self.idx = idx

class PreEncoder():

    # encoders is a dictionary type:(name, encoder_function)
    def __init__(self, encoders = {}):
        # TODO: sanity check: encoders keys must be the native string type
        self.ids = {}  # dictionary of id:id_new for recurring items in data
        self.slots = []
        self.encoders = encoders   # name:type pairs
        self.encoders_types = tuple(encoders.keys())
        # basictypes: don't walk these types:
        self.basictypes = [int, float, type(None)]
        self.basictypes = tuple(self.basictypes)

    def obj_slot(self, obj):
        if isinstance(obj, self.basictypes):
            # Basic types get a slot, but they're already done then. Also,
            # basic types don't have an associated id(x).
            slot = Slot(obj, len(self.slots))
            slot.done = True
            slot.encoded = obj
            self.slots.append(slot)
            return slot
        obj_id = id(obj)
        if obj_id in self.ids:
            idx = self.ids[obj_id]
            return self.slots[idx]
        slot = Slot(obj, len(self.slots))
        self.ids[obj_id] = len(self.slots)
        self.slots.append(slot)
        return slot

    def apply_encoders(self, obj):
        encoder_name = self.encoders[type(obj)][0]
        encoder_func = self.encoders[type(obj)][1]
        data_init, data_final = encoder_func(obj)
        # TODO: sanity check: encode_name MUST be native str type
        # (This should already be done when setting up the PreEncoder class)
        encoding_tag = 'py/' + encoder_name
        encoder_params = [data_init]
        if not data_final is None:
            encoder_params.append(data_final)
        return encoding_tag, encoder_params

    def walk(self, obj):
        slot = self.obj_slot(obj)
        if not slot.done:
            slot.done = True  # Don't have to walk it again, because we'll do it now
            if isinstance(obj, str_types):
                slot.encoded = encode_str(obj)
            elif isinstance(obj, list):
                subslots = [None] * len(obj)  # only needed for debugging
                slot.encoded = [None] * len(obj)
                for k, item in enumerate(obj):
                    if isinstance(item, self.basictypes):
                        slot.encoded[k] = item
                    else:
                        subslot = self.walk(item)
                        subslots[k] = subslot
                        slot.encoded[k] = [subslot.idx]
            elif isinstance(obj, dict):
                subslots = [None] * len(obj)
                slot.encoded = ['py/'] + [None] * len(obj)
                for k, key in enumerate(obj.keys()):
                    kv_obj = [key, obj[key]]
                    subslot = self.walk(kv_obj)
                    subslots[k] = subslot
                    slot.encoded[k + 1] = subslot.idx
            elif isinstance(obj, self.encoders_types):
                encoding_tag, encoder_params = self.apply_encoders(obj)
                # encoder_params is a list with length 1 or 2
                params_slots = [self.walk(param) for param in encoder_params]
                params_slots = [param_slot.idx for param_slot in params_slots]
                slot.encoded = [encoding_tag] + params_slots
            else:
                raise NeverHappens
        return slot

    def encode(self, obj):
        self.walk(obj)
        return [slot.encoded for slot in self.slots]


if str_mode == 'bytes':
    re_deserializer0 = re.compile('py/(.*)')
    re_deserializer1 = re.compile(u'py/(.*)')
    def deserializer_match(s):
        if isinstance(s, bytes):
            return re_deserializer0.match(s)
        else:
            return re_deserializer1.match(s)
else:  # str_mode == 'unicode'
    re_deserializer0 = re.compile('py/(.*)')
    re_deserializer1 = re.compile(b'py/(.*)')
    def deserializer_match(s):
        if isinstance(s, bytes):
            return re_deserializer1.match(s)
        else:
            return re_deserializer0.match(s)


# TODO:
# "py/..."  and "py/" need to be escaped  (to "_py" to prevent lengthening)

# TODO: How does future.unicode_literals affect this??


class PostDecoder():

    # decoders is a dictionary name:(decoder_function)
    def __init__(self, decoders = {}):
        self.slots = []
        self.decoders = decoders   # name:(object_creation_fn, object_configure_fn) pairs
        self.decoders_names = tuple(decoders.keys())
        self.basictypes = [int, float, type(None)]  # don't walk these types
        self.basictypes = tuple(self.basictypes)

    def decode(self, encoded_list):
        self.slots = [None] * len(encoded_list)
        for k, encoded in enumerate(encoded_list):
            slot = Slot(None, k)
            slot.encoded = encoded
            self.slots[k] = slot
        self.walk(self.slots[0])
        return self.slots[0].raw

    # Mark object into ids dictionary
    def seen_decode(self, obj):
        if isinstance(obj, self.basictypes):
            return
        self.idcnt += 1
        self.ids[self.idcnt] = obj

    def reserve_id(self):
        self.idcnt += 1
        self.ids[self.idcnt] = Reserve()
        return self.idcnt

    def fill_reservation(self, idd, obj):
        self.ids[idd] = obj

    def calculate_deserializer(self, encoded):
        decoder_init_fn = None
        decoder_final_fn = None
        deserial_obj = None
        if len(encoded) > 1 and isinstance(encoded[0], str_types):
            strn = force_str_type0(encoded[0])
            if strn == 'py/':
                return dict, None, None
            check_pytype = deserializer_match(strn)
            if not check_pytype is None:
                deserial_name = check_pytype.groups()[0]
                deserial_name = force_str_type0(deserial_name)
                if not deserial_name in self.decoders:
                    raise Exception("Don't know how to decode py/%s" % deserial_name)
                decoder_init_fn, decoder_final_fn = self.decoders[deserial_name]
        return decoder_init_fn, decoder_final_fn, deserial_obj

    def walk(self, slot):
        if not slot.done:
            slot.done = True
            if not isinstance(slot.encoded, list):
                if not isinstance(slot.encoded, str_types):
                    # basic type
                    slot.raw = slot.encoded
                else:
                    slot.raw = decode_str(slot.encoded)
                return
            else:
                (decoder_init_fn, decoder_final_fn, deserial_obj
                    ) = self.calculate_deserializer(slot.encoded)
            if not decoder_init_fn:
                # Plain list
                slot.raw = [None] * len(slot.encoded)
                for k, item in enumerate(slot.encoded):
                    if not isinstance(item, list):
                        # Has to be a basic type
                        slot.raw[k] = item
                    else:
                        idx = item[0]
                        self.walk(self.slots[idx])
                        slot.raw[k] = self.slots[idx].raw
            elif decoder_init_fn == dict:
                # Dictionary
                slot.raw = {}
                for kv_idx in slot.encoded[1:]:
                    self.walk(self.slots[kv_idx])
                    key, value = self.slots[kv_idx].raw
                    slot.raw[key] = value
            else:
                # Custom decoder
                if not len(slot.encoded) in (2, 3):
                    raise Exception('Unexpected error on slot %d' % slot.idx)
                init_idx = slot.encoded[1]
                self.walk(self.slots[init_idx])
                init_slot = self.slots[init_idx]
                init_params = init_slot.raw
                slot.raw = decoder_init_fn(init_params)
                if slot.raw is None:
                    raise Exception('Cannot provide init decoder that returns None')
                if len(slot.encoded) == 3:
                    final_idx = slot.encoded[2]
                    self.walk(self.slots[final_idx])
                    final_slot = self.slots[final_idx]
                    final_params = final_slot.raw
                    raw2 = decoder_final_fn(slot.raw, final_params)
                    if slot.raw is None:
                        slot.raw = raw2
                    elif not slot.raw is raw2:
                        raise Exception('Object finalizer function must return the same object')


def encode_tuple(obj):
    return list(obj), None


def decode_tuple(config):
    return tuple(config)


def encode_np_ndarray(obj):
    if not isinstance('', bytes):
        data_key = 'data'
        obj_init = [
            ['dtype', obj.dtype.name], 
            ['shape', obj.shape], 
        ]
    else:
        data_key = b'data'
        obj_init = [
            [b'dtype', obj.dtype.name.encode()],
            [b'shape', obj.shape], 
        ]
    obj_final = None
    if obj.dtype.name == 'object':
        obj_init.append([data_key, obj[()]])
        obj_final = obj_init[1:]
        obj_init = obj_init[:1]
    else:
        obj_init.append([data_key, obj.tobytes()])
    return obj_init, obj_final


def decode_np_ndarray_init(config):
    config = dict(config)
    force_str_type0_keys(config)

    if not config['dtype'] == 'object':
        obj = np.fromstring(config['data'], dtype = config['dtype'])
        obj = obj.reshape(config['shape'])
    else:
        obj = np.array(None, dtype = 'object')
    return obj


def decode_np_ndarray_final(obj, config):
    if not config is None:  # only when it was an the special np.object
        config = dict(config)
        obj[()] = config['data']
    return obj


def encode_bytes(obj):
    enc0 = obj.decode('latin1'); enc1 = b64encode(obj).decode('latin1')
    if len(json.dumps(enc0)) < len(json.dumps(enc1)):
        return [0, enc0], None
    else:
        return [1, enc1], None


def decode_bytes(obj):
    if obj[0] == 0:
        return obj[1].encode('latin1')
    elif obj[0] == 1:
        return b64decode(obj[1])
    else:
        raise NeverHappens


def encode_unicode(obj):
    return obj.encode(), None


def decode_unicode(obj):
    if isinstance(obj, bytes):
        return obj.decode()
    return obj
