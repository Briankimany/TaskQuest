
import logging
from app.config import app_folder
from functools import wraps
from flask import request, jsonify
from werkzeug.exceptions import HTTPException
from app.utils.exceptions import AppError

class LoggerManager:
    def __init__(self, log_file="app.log", log_level=logging.DEBUG, logger_name=None):
        self.logger = logging.getLogger(logger_name)  
        self.logger.setLevel(log_level)

        log_file = app_folder.parent /'logs'/log_file
        log_file.parent.mkdir(exist_ok = True , parents=True)
    
        file_handler = logging.FileHandler(log_file)  
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger


auth_logger = LoggerManager(log_file='auth_logs.log',
                            logger_name='rpg_auth',
                            log_level=logging.DEBUG).get_logger()
api_logger = LoggerManager(log_file='api.logs',logger_name='api_logger',
                           log_level=logging.DEBUG).get_logger()

external_apis_logger = LoggerManager(log_file='api_external.logs',logger_name='external_apis',
                           log_level=logging.DEBUG).get_logger()


