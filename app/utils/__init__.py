
"""
A module to hold util funcion and classed for the project
"""

from .routes_api_utils import login_required,general_decorator 
from .managers.timetable_manager import TimetableManager

from .decorators import ApiDecorators