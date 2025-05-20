
from flask import session  ,request

from functools import wraps
from app.config import TESTING_USER_ID ,TESTING_KEY
from app.utils.custom_errors import AuthorizationError ,AppError
from app.utils.logger import auth_logger ,api_logger

from werkzeug.exceptions import HTTPException
import os 

class ApiDecorators:
    def __init__(self, dec_constructors: list, base_function: callable):
        self.base_function = base_function
        self.dec_constructors = dec_constructors

    def __call__(self, *args, **kwargs):
        func = self.base_function

        for decorator in reversed(self.dec_constructors):
            func = decorator(func)

        return func(*args, **kwargs)

    def build(self):
        @wraps(self.base_function)
        def wrapper(*args, **kwargs):
            return self(*args, **kwargs)
        return wrapper

    @classmethod
    def construct_login_wrapper(cls):
        def decorator(func):
            def login_wrapper(*args, **kwargs):
                try:
        
                    if 'user_id' not in session:
                        if TESTING_KEY != request.args.get('tkn'):
                            auth_logger.warning("Unauthorized access attempt", extra={'user': 'SYSTEM'})
                            raise AuthorizationError("Un-authorized access", 403)

                        auth_logger.info(
                            f"Test session activated for user {TESTING_USER_ID}",
                            extra={'user': 'TESTING'}
                        )
                        session['user_id'] = TESTING_USER_ID
                        try:
                            return func(*args, **kwargs)
                        finally:
                            session.pop('user_id')
                            auth_logger.info("Test session cleared", extra={'user': 'TESTING'})
                    else:
                        auth_logger.info(
                            f"Authorized access by {session['user_id']}",
                            extra={'user': session['user_id']}
                        )
                        return func(*args, **kwargs)
                except AuthorizationError as e:
                    auth_logger.error(
                        f"Auth failure: {str(e)}",
                        extra={'user': session.get('user_id', 'UNKNOWN')},
                        exc_info=True
                    )
                    raise
            return login_wrapper
        return decorator

    @classmethod
    def construct_logger_wrapper(cls):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except AppError as e:
                    api_logger.error(
                        f"{e.__class__.__name__}: {str(e)} | URL: {request.url} | Method: {request.method} | Body: {request.get_json(silent=True)}"
                    )
                    raise
                except HTTPException as e:
                    api_logger.error(
                        f"HTTPException: {str(e)} | URL: {request.url} | Method: {request.method} | Body: {request.get_json(silent=True)}"
                    )
                    raise
                except Exception as e:
                    api_logger.exception(
                        f"Unhandled Exception: {str(e)} | URL: {request.url} | Method: {request.method} | Body: {request.get_json(silent=True)}",
                        stack_info=False
                    )
                    raise
            return wrapper
        return decorator