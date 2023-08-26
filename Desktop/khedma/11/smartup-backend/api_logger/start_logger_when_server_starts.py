import threading

from api_logger.insert_log_into_database import InsertLogIntoDatabase

LOG_THREAD_NAME = "insert_log_into_database"
logger_thread = None

already_exists = False

for t in threading.enumerate():
    if t.name == logger_thread:
        already_exists = True
        break

if not already_exists:
    t = InsertLogIntoDatabase()
    t.daemon = True
    t.name = logger_thread
    t.start()
    logger_thread = t
