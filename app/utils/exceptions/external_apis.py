
from .custom_errors import AppError

class ExternalAPIError(AppError):
    """
    Base error for external API operations.
    Inherits from AppError and adds API-specific context.
    """
    def __init__(self, message="API request failed", status_code=500,extra_data={},endpoint=None, method=None, response=None):
        data = {
            'endpoint': endpoint,
            'method': method,
            'api_response': response
        }
        data.update(extra_data)
        super().__init__(message, status_code,data)

class AssistantError(ExternalAPIError):
    """
    Specialized error for LLM Assistant operations.
    """
    def __init__(self, message="LLM Assistant operation failed", status_code=500, 
                 prompt_key=None, model=None, llm_request=None,response=None):
        extra_data = {
            'prompt_key': prompt_key,
            'model': model,
            'llm_request': self._sanitize_request(llm_request)
        }
        super().__init__(message, status_code, extra_data=extra_data,response=response)
    
    def _sanitize_request(self, request):
       
        if not request:
            return None
        if 'messages' in request:
            return {
                'model': request.get('model'),
                'message_count': len(request['messages'])
            }
        return request