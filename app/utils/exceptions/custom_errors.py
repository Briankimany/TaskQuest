"""
Module to hold My custom errors 
"""

class AppError(Exception):
    def __init__(self, message="An error occurred", status_code=500,extra_data={}):
        self.message = message
        self.status_code = status_code
        self.extra_data = extra_data

        super().__init__(message)

    def to_response(self):
        resp = {}
        error_data = {
                'type': self.__class__.__name__,
                'description': repr(self),
                'msg': str(self)
            }
    
        if self.extra_data:
            resp[self.__class__.__name__.lower()]=self.extra_data
            resp.update(error_data)
        else:
            resp.update(error_data)

        return resp ,self.status_code
    
    
class AuthorizationError(AppError):
    def __init__(self, message="Unauthorized access",status_code=403):
        super().__init__(message, status_code=status_code)

class RecordNotFoundError(AppError):
    def __init__(self, message="Record not found",status_code=404):
        super().__init__(message, status_code=status_code)
class RecordDuplicationError(AppError):
    def __init__(self, message="Duplication error", status_code=409):
        super().__init__(message, status_code)
    
class InvalidRequestData(AppError):
    def __init__(self, message="Invalid request data",status_code=400):
        super().__init__(message, status_code)

class TaskScheduleError(AppError):
    def __init__(self, message="An error occurred and could not schedule", status_code=409):
        super().__init__(message, status_code)
        
class IncompleteTasks(AppError):
    def __init__(self, message="System found incomplete tasks", status_code=409, extra_data={}):
        super().__init__(message, status_code, extra_data)

class CustomWarnings(AppError):
    def __init__(self, message="request successful but should there are some warnings. ", status_code=207,extra_data={}):
        super().__init__(message, status_code,extra_data=extra_data)


