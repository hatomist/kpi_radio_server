import threading
import time
from typing import Dict, Union
import icecastplayer
import schedule


class RadioSchedule:
    def __init__(self, radio_schedule, radio: icecastplayer.IcecastPlayer):
        # schedule in format: {"monday": {"09:00": {"radio_mode": 0, "air_time": "Утренний эфир"}}}
        self.__schedule: Dict[str, Dict[str, Dict[str, Union[str, int]]]] = radio_schedule
        self.__cease_continuous_run = None
        self.__radio = radio
        self.set_schedule(self.__schedule)

    @staticmethod
    def __run_scheduler_continuously(interval: int = 1):
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

    def set_schedule(self, radio_schedule: Dict[str, Dict[str, Dict[str, Union[str, int]]]]):
        self.__schedule = radio_schedule
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            for at_time in self.__schedule[day].keys():
                do_job_scheduled = getattr(schedule.every(), day).at(at_time).do
                job = (self.__radio.set_radio_mode, self.__radio.set_auto_mode, None,
                       self.__radio.set_announcement_mode,
                       self.__radio.set_off_mode)[self.__schedule[day][at_time]['radio_mode']]
                do_job_scheduled(lambda x_day=day, x_at_time=at_time:
                                 job(self.__schedule[x_day][x_at_time]['air_time']))

    def start(self):
        self.__cease_continuous_run = self.__run_scheduler_continuously()

    def stop(self):
        self.__cease_continuous_run.set()
