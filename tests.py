
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
        if str_mode == 'bytes':
            data2_expect = ['b' + data]
        else:
            data2_expect = ['u' + data]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_default_string, 'Encode default string'))
        
    def test_alt_string():
        if str_mode == 'bytes':
            data = u'hello!'
            data2_expect = ['uhello!']
        else:
            data = b'hello!'
            data2_expect = ['bhello!']
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
            data2_expect = [['py/np_ndarray', 1], [[2], [5], [9]], [[3], [4]],
                'bdtype', 'bint64', [[6], [7]], 'bshape', ['py/tuple', 8], [2,
                2], [[10], [11]], 'bdata', 'b\x01\x00\x00\x00\x00\x00\x00\x00'
                '\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00'
                '\x00\x04\x00\x00\x00\x00\x00\x00\x00']
        else: # unicode
            data2_expect = [['py/np_ndarray', 1], [[2], [5], [9]], [[3], [4]],
                'udtype', 'uint64', [[6], [7]], 'ushape', ['py/tuple', 8], [2,
                2], [[10], [11]], 'udata', 'b\x01\x00\x00\x00\x00\x00\x00\x00'
                '\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00'
                '\x00\x04\x00\x00\x00\x00\x00\x00\x00']
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert (data == data3).all()
    tests.append((test_encode_np_array, 'Encode numpy array'))

    def test_encode_np_object_array():
        data = np.array({1: 2, 3: 4})
        data2 = PreEncoder(default_encode_settings).encode(data)
        if str_mode == 'bytes':
            data2_expect = [['py/np_ndarray', 1, 5], [[2]], [[3], [4]],
                'bdtype', 'bobject', [[6], [10]], [[7], [8]], 'bshape', [
                'py/tuple', 9], [], [[11], [12]], 'bdata', ['py/', 13, 14], [1,
                2], [3, 4]]
        else:
            data2_expect = [['py/np_ndarray', 1, 5], [[2]], [[3], [4]],
                'udtype', 'uobject', [[6], [10]], [[7], [8]], 'ushape', [
                'py/tuple', 9], [], [[11], [12]], 'udata', ['py/', 13, 14], [1,
                2], [3, 4]]
        assert data2 == data2_expect
        data3 = PostDecoder(default_decode_settings).decode(data2)
        assert data == data3
    tests.append((test_encode_np_object_array, 'Encode numpy object array'))

    def test_circular_np():
        data = np.array({123: None})
        data[()][123] = data  # now circular
        data2 = PreEncoder(default_encode_settings).encode(data)
        if str_mode == 'bytes':
            s_prefix = 'b'
        else:
            s_prefix = 'u'
        s_dtype = s_prefix + 'dtype'
        s_object = s_prefix + 'object'
        s_shape = s_prefix + 'shape'
        s_data = s_prefix + 'data'
        data2_expect = [
            ['py/np_ndarray', 1, 5],  # 0
            [[2]],                    # 1
            [[3], [4]],               # 2
            s_dtype,                  # 3
            s_object,                 # 4
            [[6], [10]],              # 5
            [[7], [8]],               # 6
            s_shape,                  # 7
            ['py/tuple', 9],          # 8
            [],                       # 9
            [[11], [12]],             # 10
            s_data,                   # 11
            ['py/', 13],              # 12
            [123, [0]]]               # 13
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

if __name__ == '__main__':
    run_tests()
