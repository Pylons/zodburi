TRUETYPES = ('1', 'on', 'true', 't', 'yes')
FALSETYPES = ('', '0', 'off', 'false', 'f', 'no')


class SuffixLengthMismatch(ValueError):
    def __init__(self, d):
        self.d = d
        super().__init__("All suffix keys must have the same length")


class SuffixMultiplier:
    """Convert integer-like strings w/ size suffixes to integers

    - 'd' is a dictionary of suffixes to integer multipliers.
    - 'default' is the multiplier if no suffixes match.

    Matches are case insensitive.

    Returned values are in the fundamental unit.
    """
    def __init__(self, d, default=1):
        # all keys must be the same size
        sizes = set(len(key) for key in d)

        if len(sizes) > 1:
            raise SuffixLengthMismatch(d)

        self._d = {key.lower(): value for key, value in d.items()}
        self._default = default
        self._keysz = sizes.pop() if sizes else 0

    def __call__(self, v):
        if self._keysz and len(v) > self._keysz:
            v = v.lower()
            suffix = v[-self._keysz:]
            multiplier = self._d.get(suffix, self._default)

            if multiplier is not self._default:
                v = v[:-self._keysz]
        else:
            multiplier = self._default

        return int(v) * multiplier


convert_bytesize = SuffixMultiplier({
    "kb": 1024,
    "mb": 1024*1024,
    "gb": 1024*1024*1024,
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
    return tuple(value.split(","))
