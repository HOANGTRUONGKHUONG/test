import logging

from app.setting import MONITOR_LOG_DIR


# def logger(log_name):
#     log_writer = logging.getLogger('waf_log')
#     while log_writer.handlers:
#         log_writer.handlers.pop()
#     if "/" in log_name:
#         handler = logging.FileHandler(log_name)
#     else:
#         handler = logging.FileHandler(f"{MONITOR_LOG_DIR}/{log_name}.log")
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     log_writer.addHandler(handler)
#     log_writer.setLevel(logging.INFO)
#     # handler.close()
#     return log_writer

class c_logger:
    def __init__(self, log_name): 
        self.log_writer = logging.getLogger('waf_log')
        while self.log_writer.handlers:
            self.log_writer.handlers.pop()
        if "/" in log_name:
            self.handler = logging.FileHandler(log_name)
        else:
            self.handler = logging.FileHandler(f"{MONITOR_LOG_DIR}/{log_name}.log")
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log_writer.setLevel(logging.INFO)
    def __enter__(self):
        logger=c_logger()
        logger.log_writer.addHandler(self.handler)
        return logger
    def __exit__(self,exc_type,exc_val,exc_tb):
        for handler in self.log_writer.handlers[:]:
            handler.close()
            self.log_writer.removeHandler(handler)
