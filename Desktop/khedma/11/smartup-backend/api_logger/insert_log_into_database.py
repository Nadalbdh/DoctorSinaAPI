import time
from queue import Queue
from threading import Thread

from django.conf import settings

from api_logger.models import APILog


class InsertLogIntoDatabase(Thread):
    def __init__(self):
        super().__init__()
        self.DRF_LOGGER_QUEUE_MAX_SIZE = settings.DRF_LOGGER_QUEUE_MAX_SIZE
        self.DRF_LOGGER_INTERVAL = settings.DRF_LOGGER_INTERVAL
        self._queue = Queue(maxsize=self.DRF_LOGGER_QUEUE_MAX_SIZE)

    def run(self):
        self.start_queue_process()

    def put_log_data(self, data):
        self._queue.put(APILog(**data))

        if self._queue.qsize() >= self.DRF_LOGGER_QUEUE_MAX_SIZE:
            self._start_bulk_insertion()

    def start_queue_process(self):
        while True:
            time.sleep(self.DRF_LOGGER_INTERVAL)
            self._start_bulk_insertion()

    def _start_bulk_insertion(self):
        bulk_item = []
        while not self._queue.empty():
            bulk_item.append(self._queue.get())
        if bulk_item:
            self._insert_into_data_base(bulk_item)

    def _insert_into_data_base(self, bulk_item):
        try:
            APILog.objects.bulk_create(bulk_item)
        except Exception as e:
            print("DRF API LOGGER EXCEPTION:", e)
