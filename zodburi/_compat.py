try:
    from urllib.parse import parse_qsl
except ImportError: #pragma NO COVER
    from cgi import parse_qsl

try:
    from urllib.parse import quote
except ImportError: #pragma NO COVER
    from urllib import quote

try:
    from urllib.parse import urlsplit
except ImportError: #pragma NO COVER
    from urlparse import urlsplit
