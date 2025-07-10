import logging
import sys

LOG_LEVEL = logging.DEBUG

# Initialize the log handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(LOG_LEVEL)

# Specify the log format
formatter = logging.Formatter("%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
handler.setFormatter(formatter)

# Initialize the root logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.addHandler(handler)
