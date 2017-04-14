
from __future__ import print_function

import numpy as np
import p23serialize

from p23serialize import (
    PreEncoder, PostDecoder, decode_bytes, encode_np_ndarray, decode_tuple,
    encode_tuple, decode_np_ndarray_init, decode_np_ndarray_final, encode_bytes,
    encode_unicode, decode_unicode, str_mode)

def run_tests():
    tests = []
    
    default_encode_settings = {
        tuple: ('tuple', encode_tuple),
        np.ndarray: ('np_ndarray', encode_np_ndarray)
    }
    default_decode_settings = {
        'np_ndarray': (decode_np_ndarray_init, decode_np_ndarray_final),
        'tuple': (decode_tuple, None)
    }
    if str_mode == 'unicode':
        default_encode_settings[bytes] = ('bytes', encode_bytes)
        default_decode_settings['bytes'] = (decode_bytes, None)
    else:  # str_mode == 'bytes'
        default_encode_settings[unicode] = ('unicode', encode_unicode)
        default_decode_settings['unicode'] = (decode_unicode, None)

    def test_tuple():
        data = (1, 2, 3)
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [['py/tuple', 1], [1, 2, 3]]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_tuple, 'Encode tuple'))

    def test_list():
        data = [1, 2, 3]
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [[1, 2, 3]]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_list, 'Encode list'))

    def test_default_string():
        data = 'hello!'
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [data]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_default_string, 'Encode default string'))
        
    def test_alt_string():
        if str_mode == 'bytes':
            data = u'hello!'
            data2_expect = [['py/unicode', 1], 'hello!']
        else:
            data = b'hello!'
            data2_expect = [['py/bytes', 1], [0, 'hello!']]
        data2 = PreEncoder(default_encode_settings).encode(data)
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_alt_string, 'Encode alternative string'))

    def test_encode_dict():
        data = {1: 2, 3: 4}
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [['py/', 1, 2], [1, 2], [3, 4]]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_encode_dict, 'Encode dict'))

    def test_encode_int():
        data = 123
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [123]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_encode_int, 'Encode int'))

    def test_encode_None():
        data = None
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [None]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_encode_None, 'Encode None'))

    def test_encode_np_array():
        data = np.array([[1,2], [3,4]])
        data2 = PreEncoder(default_encode_settings).encode(data)
        if str_mode == 'bytes':
            data2_expect = [['py/np_ndarray', 1], [[2], [3], [6]], ['dtype',
                'int64'], ['shape', [4]], ['py/tuple', 5], [2, 2], ['data',
                '\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00'
                '\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00'
                '\x00\x00']]
        else: # unicode
            data2_expect = [['py/np_ndarray', 1], [[2], [3], [6]], ['dtype',
                'int64'], ['shape', [4]], ['py/tuple', 5], [2, 2], ['data', [7]
                ], ['py/bytes', 8], [1,
                'AQAAAAAAAAACAAAAAAAAAAMAAAAAAAAABAAAAAAAAAA=']]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert (data == data3).all()
    tests.append((test_encode_np_array, 'Encode numpy array'))

    def test_encode_np_object_array():
        data = np.array({1: 2, 3: 4})
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [['py/np_ndarray', 1, 3], [[2]], ['dtype', 'object'],
            [[4], [7]], ['shape', [5]], ['py/tuple', 6], [], ['data', [8]],
            ['py/', 9, 10], [1, 2], [3, 4]]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_encode_np_object_array, 'Encode numpy object array'))

    def test_circular_np():
        data = np.array({123: None})
        data[()][123] = data  # now circular
        data2 = PreEncoder(default_encode_settings).encode(data)
        data2_expect = [
            ['py/np_ndarray', 1, 3],  # 0
            [[2]],                    # 1
            ['dtype', 'object'],      # 2
            [[4], [7]],               # 3
            ['shape', [5]],           # 4
            ['py/tuple', 6],          # 5
            [],                       # 6
            ['data', [8]],            # 7
            ['py/', 9],               # 8
            [123, [0]]]               # 9
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        # PS cannot do assert data == data3
        # (python itself goes into an infinite recursion)
        # Alternative test...
        assert id(data3) == id(data3[()][123])
    tests.append((test_circular_np, 'Encode circular numpy object array'))


    # test09: encode unknown type (must fail in specific way)
    # TODO: tests between python2/3 and bytes/str/unicode

    # tests: json, msgpack


    for test, test_description in tests:
        print('Test:', test_description)
        test()

run_tests()
