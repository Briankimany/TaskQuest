from .custom_errors import *
from .external_apis import *

from flask import jsonify


def make_error_response(error: Exception, msg: str = "", code: int = 500):
    """Generic fallback for unexpected exceptions."""
    data = {
        'type': type(error).__name__,
        'description': repr(error),
        'msg': msg or str(error)
    }
    return jsonify(data), code
