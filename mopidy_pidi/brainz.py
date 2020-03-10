"""
Musicbrainz related functions.
"""
import base64
import logging
import os
import time
from threading import Thread

import musicbrainzngs as mus

from .__init__ import __version__

logger = logging.getLogger(__name__)


class Brainz:
    def __init__(self, cache_dir):
        """Initialize musicbrainz."""
        mus.set_useragent(
            "python-pidi: A cover art daemon.",
            __version__,
            "https://github.com/pimoroni/mopidy-pidi",
        )

        self._cache_dir = cache_dir
        self._default_filename = os.path.join(self._cache_dir, "__default.jpg")

        self.save_album_art(self.get_default_album_art(), self._default_filename)

    def get_album_art(self, artist, album, callback=None):
        if artist is None or album is None or artist == "" or album == "":
            if callback is not None:
                return callback(self._default_filename)
            return self._default_filename

        file_name = self.get_cache_file_name(f"{artist}_{album}")

        if os.path.isfile(file_name):
            # If a cached file already exists, use it!
            if callback is not None:
                return callback(file_name)
            return file_name

        if callback is not None:

            def async_request_album_art(self, artist, album, file_name, callback):
                album_art = self.request_album_art(artist, album)

                if album_art is None:
                    # If the MusicBrainz request fails, cache the default
                    # art using this filename.
                    self.save_album_art(self.get_default_album_art(), file_name)
                    return callback(file_name)

                self.save_album_art(album_art, file_name)

                return callback(file_name)

            t_album_art = Thread(
                target=async_request_album_art,
                args=(self, artist, album, file_name, callback),
            )
            t_album_art.start()
            return t_album_art

        else:
            album_art = self.request_album_art(artist, album)

            if album_art is None:
                # If the MusicBrainz request fails, cache the default
                # art using this filename.
                self.save_album_art(self.get_default_album_art(), file_name)
                return file_name

            self.save_album_art(album_art, file_name)

            return file_name

    def save_album_art(self, data, output_file):
        with open(output_file, "wb") as f:
            f.write(data)

    def request_album_art(self, artist, album, size=500, retry_delay=5, retries=5):
        """Download the cover art."""
        try:
            data = mus.search_releases(artist=artist, release=album, limit=1)
            release_id = data["release-list"][0]["release-group"]["id"]
            logger.info("mopidy-pidi: musicbrainz using release-id: {release_id}")

            return mus.get_release_group_image_front(release_id, size=size)

        except mus.NetworkError:
            if retries == 0:
                # raise mus.NetworkError("Failure connecting to MusicBrainz.org")
                return None
            logger.info(
                f"mopidy-pidi: musicbrainz retrying download. {retries} retries left!"
            )
            time.sleep(retry_delay)
            self.request_album_art(artist, album, size=size, retries=retries - 1)

        except mus.ResponseError:
            logger.info(
                f"mopidy-pidi: musicbrainz couldn't find album art for {artist} - {album}"
            )
            return None

    def get_cache_file_name(self, file_name):
        file_name = file_name.encode("utf-8")
        file_name = base64.b64encode(file_name)
        if type(file_name) is bytes:
            file_name = file_name.decode("utf-8")
        # Ruh roh, / is a vaild Base64 character
        # but also a valid UNIX path separator!
        file_name = file_name.replace("/", "-")
        file_name = f"{file_name}.jpg"

        return os.path.join(self._cache_dir, file_name)

    def get_default_album_art(self):
        """Return binary version of default album art."""
        return base64.b64decode(
            """
iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAMAAAAM7l6QAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFn
ZVJlYWR5ccllPAAAAMBQTFRFBHwvBSl8d04DCQ99egJLfAMzejQGcGoAAGZ6AHN3N3wBSHwBKXwDAHlp
NQF9AHtXAFV7VwB7HgN9B30aG30FXncAAXtERwB8fQMbZQB5AUF8fRsHQ04rfQgLFlZTVzgteABiZ14F
agNiAmpoF3kaLVU4V1QVYhdFLkZIQy1MFWc/biYkKSVpLWUmLjVYcQBzJHMbeRQiBWxZBlxnOmkXDn0M
WAdnGhd5FkBlSRZfCk1rO3MMTmwJCm5FQgtwMhJydzVfDgAAAYtJREFUeNpUzeligjAQBOCNgFcVFVRQ
FC3gUU/Uingg7/9W3U1CpJOf38wGGpQ2ptPpDIcAYNv29Xrt9/utVqsJXBsfLmmzKbiYy3WZ6/XC1fyj
X8iiIOZQsFDBvFBct+1I6BcGuvUuedgIwzOfR9dI6QC6FF4I2+dsmEEURVIHA+RxVzZwfs4gi+JW3Hwi
ch5juF8ul/CcbTZxHD+ffFqwrGDB32z2+9/n6/VCqw1qwMZMFh6Ph+/7C2RUJAowGWqlqb9eLCa/y2/M
f2YsZWl6WK8nk+VSOTBN05iGemO73e5w+JnNZpVlRQYIKTcM+g/xtiq1BloR5Dy/3++r7ba6rWLkmmLd
LCvP8zfqCp0zNYgtepZlmu93kiCfTifP87iDNK5OkiSBbpyEe1WPs0DTdJxeEAQr3TCUgyXUQnR6ySgI
dJy7rjclV8y3PdS5jm647nRKDVBIOjoSG4KpAOpfB3V0nM/LjmyapXHBriscylrwx0FpiQ11Hf6PyXX5
ORWAoxqr44Y4/ifAAPd/TAMIg8r1AAAAAElFTkSuQmCC"""
        )
