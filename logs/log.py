# -------------------------------------------------------------------------------------------------------------

import logging

# -------------------------------------------------------------------------------------------------------------

class Logger:
    """
    A simple logger class that writes log messages to a file.

    Attributes:
        logger (logging.Logger): The logger instance used to log messages.
    """
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
        """
        Logs a message with the info level.

        Args:
            message (str): The message to log.
        """
        self.logger.info(message)    
        
# -------------------------------------------------------------------------------------------------------------