from . import str_mode

if str_mode == 'bytes':
    unicode_type = unicode
else:  # str_mode == 'unicode'
    unicode_type = str

def recursive_unicode(obj):
    if isinstance(obj, bytes):
        return obj.decode('latin1')
    elif isinstance(obj, list):
        return [recursive_unicode(_) for _ in obj]
    else:
        return obj

def recursive_bytes(obj):
    if isinstance(obj, unicode_type):
        return obj.encode('latin1')
    elif isinstance(obj, list):
        return [recursive_bytes(_) for _ in obj]
    else:
        return obj
