# -------------------------------------------------------------------------------------------------------------

import logging

# -------------------------------------------------------------------------------------------------------------

class Logger:
    def __init__(self, *, filename : str) -> None:
        self.logger = logging.getLogger(filename)
        filepath = "logs/outputs/" + filename + ".log"
        if not self.logger.handlers:
            handler = logging.FileHandler(filepath)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
    # ---------------------------------------------------------------------------------------------------------
    
    def log(self, message):
        self.logger.info(message)    
        
# -------------------------------------------------------------------------------------------------------------