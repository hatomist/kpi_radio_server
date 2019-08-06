import threading
import time
from typing import Dict, Union
import icecastplayer
import schedule


class RadioSchedule:
    def __init__(self, radio_schedule, radio: icecastplayer.IcecastPlayer):
        # schedule in format: {"monday": {"09:00": {"radio_mode": 0, "air_time": "Утренний эфир"}}}
        self.__schedule: Dict[str, Dict[str, Dict[str, Union[str, int]]]] = radio_schedule
        self.__radio = radio

    @staticmethod
    def run_scheduler_continuously(interval: int = 1):
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run
