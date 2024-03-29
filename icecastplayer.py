# -*- coding: utf-8 -*-
import vlc
from dataclasses import dataclass
from os import path
from typing import Callable
EXEC_PATH = path.dirname(path.abspath(__file__))


class RadioMode:
    RADIO = 0
    AUTO_RADIO = 1
    ANNOUNCEMENT = 2
    STREAM = 3
    OFF = 4


@dataclass
class IcecastCredentials:
    server_ip: str
    server_port: int
    stream_address: str
    src_name: str
    src_password: str
    adm_name: str
    adm_password: str


@dataclass
class MediaMeta:
    title: str = None
    artist: str = None
    genre: str = None
    art_url: str = None


class IcecastPlayer:
    def __media_changed(self, event):
        media_player: vlc.MediaPlayer = self.__list_player.get_media_player()
        media: vlc.Media = media_player.get_media()
        media.parse()
        self.__current_media_meta.title = media.get_meta(vlc.Meta.Title)
        self.__current_media_meta.artist = media.get_meta(vlc.Meta.Artist)
        self.__current_media_meta.genre = media.get_meta(vlc.Meta.Genre)
        self.__current_media_meta.art_url = media.get_meta(vlc.Meta.ArtworkURL)
        if self.__media_changed_ext_handler is not None:
            self.__media_changed_ext_handler(self.__current_media_meta)

    def __init__(self, icecast_credentials: IcecastCredentials):
        self.__vlc_instance: vlc.Instance = vlc.Instance()
        self.__list_player: vlc.MediaListPlayer = self.__vlc_instance.media_list_player_new()
        self.__playlist: vlc.MediaList = self.__vlc_instance.media_list_new()
        self.__list_player.set_media_list(self.__playlist)
        self.__media_player: vlc.MediaPlayer = self.__list_player.get_media_player()
        self.__icecast_out = f':sout=#transcode{{vcodec=none,acodec=vorb,ab=128,channels=2,' \
                             f'samplerate=44100,scodec=none}}:std{{access=shout,mux=ogg,' \
                             f'dst=//{icecast_credentials.src_name}:{icecast_credentials.src_password}@' \
                             f'{icecast_credentials.server_ip}:{icecast_credentials.server_port}/' \
                             f'{icecast_credentials.stream_address}}}'
        self.__icecast_credentials = icecast_credentials
        self.__event_manager: vlc.EventManager = self.__list_player.get_media_player().event_manager()
        self.add_track(path.join(EXEC_PATH, 'media', 'tone.wav'), '')
        self.play()  # used to avoid startup problems with VLC
        self.__event_manager.event_attach(vlc.EventType.MediaPlayerMediaChanged, self.__media_changed)
        self.__current_media_meta = MediaMeta()
        self.__media_changed_ext_handler = None
        self.__radio_mode = RadioMode.RADIO
        self.__paused = False
        self.__air_time = 'Not configured'

    def add_track(self, file_path: str, from_who: str):
        track: vlc.Media = self.__vlc_instance.media_new(file_path, self.__icecast_out)
        track.parse()
        track.set_meta(vlc.Meta.Publisher, from_who)
        track.save_meta()
        self.__playlist.add_media(track)

    def play(self):
        self.__list_player.play()

    def pause(self):
        if self.__paused:
            self.__list_player.set_pause(0)
            self.__paused = False
        else:
            self.__list_player.set_pause(1)
            self.__paused = True

    def is_paused(self) -> bool:
        return self.__paused

    def skip_track(self):
        self.__list_player.next()

    def stop(self):
        self.__list_player.stop()

    def set_media_changed_handler(self, handler: Callable[[MediaMeta], None]):
        self.__media_changed_ext_handler = handler

    def set_radio_mode(self, air_time: str):
        # TODO: maybe something else
        self.__radio_mode = RadioMode.RADIO
        self.__air_time = air_time
        self.play()

    def set_announcement_mode(self, air_time: str, file_path: str, back_to_mode: int):
        # TODO: set announcement mode
        self.__radio_mode = RadioMode.ANNOUNCEMENT
        self.__air_time = air_time

    def set_stream_mode(self, air_time: str):
        # TODO: set stream mode
        self.__radio_mode = RadioMode.STREAM
        self.__air_time = air_time

    def set_off_mode(self, air_time: str):
        # TODO: maybe something else
        self.__radio_mode = RadioMode.OFF
        self.__air_time = air_time
        self.stop()

    def set_auto_mode(self, air_time: str):
        # TODO: set auto radio mode
        self.__radio_mode = RadioMode.AUTO_RADIO
        self.__air_time = air_time
