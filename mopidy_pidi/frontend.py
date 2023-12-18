import logging
import os
import threading
import time

import pykka
import requests
from mopidy import core

import netifaces

from . import Extension
from .brainz import Brainz
from .fileart import Fileart

logger = logging.getLogger(__name__)


class PiDiConfig:
    def __init__(self, config=None):
        self.rotation = config.get("rotation", 90)
        self.spi_port = 0
        self.spi_chip_select_pin = 1
        self.spi_data_command_pin = 9
        self.spi_speed_mhz = 80
        self.backlight_pin = 13
        self.size = 240
        self.blur_album_art = True


class PiDiFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.core = core
        self.config = config
        self.current_track = None
        self.directory_path = config["local"]["media_dir"]  # Fetch media directory from Mopidy config
        #self.file_art_instance = Fileart(cache_dir=Extension.get_data_dir(config), directory_path=self.directory_path)
        self.cache_dir = Extension.get_data_dir(config)
        # Provide both cache_dir and directory_path to Fileart class
        self.file_art_instance = Fileart(cache_dir=self.cache_dir, directory_path=self.directory_path)


        #self.file_art_instance = Fileart(cache_dir=Extension.get_data_dir(config))  # Create an instance of Fileart



    def on_start(self):
        self.display = PiDi(self.config)
        self.display.start()
        self.display.update(volume=self.core.mixer.get_volume().get())
        if "http" in self.config:
            ifaces = netifaces.interfaces()
            ifaces.remove("lo")

            http = self.config["http"]
            if http.get("enabled", False):
                hostname = http.get("hostname", "127.0.0.1")
                port = http.get("port", 6680)
                if hostname in ["::", "0.0.0.0"]:
                    family = (
                        netifaces.AF_INET6 if hostname == "::" else netifaces.AF_INET
                    )
                    for iface in ifaces:
                        hostname = self.get_ifaddress(iface, family)
                        if hostname is not None:
                            break
                if hostname is not None:
                    self.display.update(
                        title=f"Visit http://{hostname}:{port} to select content."
                    )
                    self.display.update_album_art(art="")

    def on_stop(self):
        self.display.stop()
        self.display = None

    def get_ifaddress(self, iface, family):
        try:
            return netifaces.ifaddresses(iface)[family][0]["addr"]
        except (IndexError, KeyError):
            return None

    def mute_changed(self, mute):
        pass

    def options_changed(self):
        self.display.update(
            shuffle=self.core.tracklist.get_random(),
            repeat=self.core.tracklist.get_repeat(),
        )

    def playlist_changed(self, playlist):
        pass

    def playlist_deleted(self, playlist):
        pass

    def playlists_loaded(self):
        pass

    def seeked(self, time_position):
        self.update_elapsed(time_position)

    def stream_title_changed(self, title):
        self.display.update(title=title)

    def track_playback_ended(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state="pause")

    def track_playback_paused(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state="pause")

    def track_playback_resumed(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state="play")

    def track_playback_started(self, tl_track):
        self.update_track(tl_track.track, 0)
        self.display.update(state="play")

    def update_elapsed(self, time_position):
        self.display.update(elapsed=float(time_position))

    def update_track(self, track, time_position=None):
        if track is None:
            track = self.core.playback.get_current_track().get()

        title = ""
        album = ""
        artist = ""

        if track.name is not None:
            title = track.name

        if track.album is not None and track.album.name is not None:
            album = track.album.name

        if track.artists is not None:
            artist = ", ".join([artist.name for artist in track.artists])

        self.display.update(title=title, album=album, artist=artist)

        if time_position is not None:
            length = track.length
            # Default to 60s long and loop the transport bar
            if length is None:
                length = 60
                time_position %= length

            self.display.update(elapsed=float(time_position), length=float(length))

        art = None

        mp3_file_path = self.file_art_instance.get_current_playing_file()

        if mp3_file_path and os.path.isfile(mp3_file_path):
            self.file_art_instance.extract_album_art(mp3_file_path)
            art = "/var/lib/mopidy/pidi/album.jpg"

        self.display.update_album_art(art=art)

    def tracklist_changed(self):
        pass

    def volume_changed(self, volume):
        if volume is None:
            return

        self.display.update(volume=volume)

def tracklist_changed(self):
    pass

def volume_changed(self, volume):
    if volume is None:
        return

    self.display.update(volume=volume)

    def tracklist_changed(self):
        pass

    def volume_changed(self, volume):
        if volume is None:
            return

        self.display.update(volume=volume)


class PiDi:
    def __init__(self, config):
        
        self.config = config
        self.cache_dir = Extension.get_data_dir(config)
        self.display_config = PiDiConfig(config["pidi"])
        self.display_class = Extension.get_display_types()[
            self.config["pidi"]["display"]
        ]
        self.idle_timeout = config["pidi"].get("idle_timeout", 0)
        self._brainz = Brainz(cache_dir=self.cache_dir)
        self._display = self.display_class(self.display_config)
        self._running = threading.Event()
        self._delay = 1.0 / 30
        self._thread = None

        self.shuffle = False
        self.repeat = False
        self.state = "stop"
        self.volume = 100
        self.progress = 0
        self.elapsed = 0
        self.length = 0
        self.title = ""
        self.album = ""
        self.artist = ""
        self._last_progress_update = time.time()
        self._last_progress_value = 0
        self._last_state_change = 0
        self._last_art = ""

    def start(self):
        if self._thread is not None:
            return

        self._running = threading.Event()
        self._running.set()
        self._thread = threading.Thread(target=self._loop)
        self._thread.start()

    def stop(self):
        self._running.clear()
        self._thread.join()
        self._thread = None
        self._display.stop()

    def _handle_album_art(self, art):
        print("art",art)
        if art != self._last_art:
            self._display.update_album_art(art)
            self._last_art = art

    def update_album_art(self, art=None):
        _album = self.title if self.album is None or self.album == "" else self.album
        if art is not None:
            if os.path.isfile(art):
                # Art is already a locally cached file we can use
                self._display.update_album_art(art)
                self._handle_album_art(art)
                return

            elif art.startswith("http://") or art.startswith("https://"):
                file_name = self._brainz.get_cache_file_name(art)
                if os.path.isfile(file_name):
                    # If a cached file already exists, use it!
                    self._handle_album_art(file_name)
                    return

                else:
                    # Otherwise, request the URL and save it!
                    response = requests.get(art)
                    if response.status_code == 200:
                        self._brainz.save_album_art(response.content, file_name)
                        self._handle_album_art(file_name)
                        return
        # TODO: if local art not there, use brainz
        #art = self._brainz.get_album_art(self.artist, _album, self._handle_album_art)

    def update(self, **kwargs):
        if "state" in kwargs or "volume" in kwargs:
            self._last_state_change = time.time()
            self._display.start()
        self.shuffle = kwargs.get("shuffle", self.shuffle)
        self.repeat = kwargs.get("repeat", self.repeat)
        self.state = kwargs.get("state", self.state)
        self.volume = kwargs.get("volume", self.volume)
        # self.progress = kwargs.get('progress', self.progress)
        self.elapsed = kwargs.get("elapsed", self.elapsed)
        self.length = kwargs.get("length", self.length)
        self.title = kwargs.get("title", self.title)
        self.album = kwargs.get("album", self.album)
        self.artist = kwargs.get("artist", self.artist)

        if "elapsed" in kwargs:
            if "length" in kwargs:
                self.progress = float(self.elapsed) / float(self.length)
            self._last_elapsed_update = time.time()
            self._last_elapsed_value = kwargs["elapsed"]

    def _loop(self):
        while self._running.is_set():
            t_idle_sec = time.time() - self._last_state_change
            if self.idle_timeout > 0 and t_idle_sec >= self.idle_timeout:
                self._display.stop()
            elif self.state == "play":
                t_elapsed_ms = (time.time() - self._last_elapsed_update) * 1000
                self.elapsed = float(self._last_elapsed_value + t_elapsed_ms)
                self.progress = self.elapsed / self.length
            self._display.update_overlay(
                self.shuffle,
                self.repeat,
                self.state,
                self.volume,
                self.progress,
                self.elapsed,
                self.title,
                self.album,
                self.artist,
            )

            self._display.redraw()
            time.sleep(self._delay)
