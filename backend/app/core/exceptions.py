class AppException(Exception):
    """Base exception for application"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class LLMException(AppException):
    """LLM related exceptions"""
    def __init__(self, message: str):
        super().__init__(message, code=500)


class JSONParseException(AppException):
    """JSON parsing exceptions"""
    def __init__(self, message: str):
        super().__init__(message, code=500)


class SearchException(AppException):
    """Search tool exceptions"""
    def __init__(self, message: str):
        super().__init__(message, code=500)


class TaskNotFoundException(AppException):
    """Task not found"""
    def __init__(self, task_id: int):
        super().__init__(f"Task {task_id} not found", code=404)
