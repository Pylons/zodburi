TRUETYPES = ('1', 'on', 'true', 't', 'yes')
FALSETYPES = ('', '0', 'off', 'false', 'f', 'no')

class SuffixMultiplier:
    # d is a dictionary of suffixes to integer multipliers.  If no suffixes
    # match, default is the multiplier.  Matches are case insensitive.  Return
    # values are in the fundamental unit.
    def __init__(self, d, default=1):
        self._d = d
        self._default = default
        # all keys must be the same size
        self._keysz = None
        for k in d.keys():
            if self._keysz is None:
                self._keysz = len(k)
            else:
                if self._keysz != len(k):
                    raise ValueError('suffix length missmatch')

    def __call__(self, v):
        v = v.lower()
        for s, m in self._d.items():
            if v[-self._keysz:] == s:
                return int(v[:-self._keysz]) * m
        return int(v) * self._default

convert_bytesize = SuffixMultiplier({'kb': 1024,
                                     'mb': 1024*1024,
                                     'gb': 1024*1024*1024,
                                    })


def convert_int(value):
    # boolean values are also treated as integers
    value = value.lower()
    if value in FALSETYPES:
        return 0
    if value in TRUETYPES:
        return 1
    return int(value)

def convert_tuple(value):
    return tuple(value.split(','))
