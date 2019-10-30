from __future__ import unicode_literals

import threading
import time
import logging
import os

from mopidy import core
from . import Extension
from .brainz import Brainz

import pykka

from pidi_display_st7789 import DisplayST7789


logger = logging.getLogger(__name__)


class PiDiConfig():
    def __init__(self, config=None):
        self.rotation = 90
        self.spi_port = 0
        self.spi_chip_select_pin = 1
        self.spi_data_command_pin = 9
        self.spi_speed_mhz = 80
        self.backlight_pin = 13
        self.size = 240
        self.blur_album_art = True


class PiDiFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(PiDiFrontend, self).__init__()
        self.core = core
        self.config = config
        self.current_track = None

    def on_start(self):
        self.display = PiDi(self.config)
        self.display.start()

    def on_stop(self):
        self.display.stop()
        self.display = None

    def mute_changed(self, mute):
        pass

    def options_changed(self):
        self.display.update(
            shuffle=self.core.tracklist.get_random(),
            repeat=self.core.tracklist.get_repeat()
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
        pass

    def track_playback_ended(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state='pause')

    def track_playback_paused(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state='pause')

    def track_playback_resumed(self, tl_track, time_position):
        self.update_elapsed(time_position)
        self.display.update(state='play')

    def track_playback_started(self, tl_track):
        self.update_track(tl_track.track, 0)
        self.display.update(state='play')

    def update_elapsed(self, time_position):
         self.display.update(
            elapsed=float(time_position),
        )
    
    def update_track(self, track, time_position=None):
        if track is None:
            track = self.core.playback.get_current_track().get()

        title = ''
        album = ''
        artist = ''

        if track.name is not None:
            title = track.name

        if track.album is not None and track.album.name is not None:
            album = track.album.name

        if track.artists is not None:
            artist = ", ".join([artist.name for artist in track.artists])

        self.display.update(
            title=title,
            album=album,
            artist=artist
        )

        if time_position is not None:
            self.display.update(
                elapsed=float(time_position),
                length=float(track.length)
            )

    def tracklist_changed(self):
        pass

    def volume_changed(self, volume):
        self.display.update(
            volume=self.core.playback.volume.get()
        )


class PiDi():
    def __init__(self, config):
        self.config = config
        self.cache_dir = Extension.get_data_dir(config)
        self.display_config = PiDiConfig(config["pidi"])
        self.display_class = Extension.get_display_types()[self.config["pidi"]["display"]]

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

    def update(self, **kwargs):
        self.shuffle = kwargs.get('shuffle', self.shuffle)
        self.repeat = kwargs.get('repeat', self.repeat)
        self.state = kwargs.get('state', self.state)
        self.volume = kwargs.get('volume', self.volume)
        # self.progress = kwargs.get('progress', self.progress)
        self.elapsed = kwargs.get('elapsed', self.elapsed)
        self.length = kwargs.get('length', self.length)
        self.title = kwargs.get('title', self.title)
        self.album = kwargs.get('album', self.album)
        self.artist = kwargs.get('artist', self.artist)

        if 'album' in kwargs or 'artist' in kwargs or 'title' in kwargs:
            _album = self.title if self.album is None or self.album == '' else self.album
            art = self._brainz.get_album_art(self.artist, _album)
            if art != self._last_art:
                print("Updating art to {}".format(art))
                self._display.update_album_art(art)
                self._last_art = art

        if 'elapsed' in kwargs:
            if 'length' in kwargs:
                self.progress = float(self.elapsed) / float(self.length)
            self._last_elapsed_update = time.time()
            self._last_elapsed_value = kwargs['elapsed']

    def _loop(self):
        while self._running.wait(self._delay):
            if self.state == 'play':
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
                self.artist)

            self._display.redraw()

