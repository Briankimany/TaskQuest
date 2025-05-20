

from datetime import datetime
import pytz
from app.utils.decorators import ApiDecorators

def login_required(func):
    return ApiDecorators(
        dec_constructors=[
            ApiDecorators.construct_login_wrapper()
        ],
        base_function=func
    ).build()


def general_decorator(func):
    return ApiDecorators(
        dec_constructors=[
            ApiDecorators.construct_logger_wrapper(),
            ApiDecorators.construct_login_wrapper(),
        ],
        base_function=func
    ).build()

def to_utc_from_user_input(
        user_datetime_str, 
        user_timezone_str,
        parsing_string,
        skip_conversion=True):

        naive_dt = datetime.strptime(user_datetime_str, parsing_string)
        if skip_conversion:
             return naive_dt
        
        user_tz = pytz.timezone(user_timezone_str)
        user_dt = user_tz.localize(naive_dt) 

        utc_dt = user_dt.astimezone(pytz.utc)
        
        return utc_dt
  
def is_valid_timezone(tz_str):
    return tz_str in pytz.all_timezones

