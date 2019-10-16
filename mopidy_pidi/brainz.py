"""
Musicbrainz related functions.
"""
import time
import musicbrainzngs as mus
import os
import base64
    
from .__init__ import __version__


class Brainz:
    def __init__(self, cache_dir):
        """Initialize musicbrainz."""
        mus.set_useragent("python-pidi: A cover art daemon.",
                          __version__,
                          "https://github.com/pimoroni/mopidy-pidi")

        self._cache_dir = cache_dir
        self._default_filename = os.path.join(self._cache_dir, "__default.jpg")

        self.save_album_art(self.get_default_album_art(), self._default_filename)

    def get_album_art(self,  artist, album):
        if artist is None or album is None or artist == "" or album == "":
            return self._default_filename

        file_name = "{artist}_{album}".format(
            artist=artist,
            album=album
        )

        file_name = "{}.jpg".format(base64.b64encode(file_name))

        file_name = os.path.join(self._cache_dir, file_name)

        if os.path.exists(file_name):
            # If a cached file already exists, use it!
            return file_name

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
            data = mus.search_releases(artist=artist,
                                       release=album,
                                       limit=1)
            release_id = data["release-list"][0]["release-group"]["id"]
            print("album: Using release-id: {}".format(data['release-list'][0]['id']))

            return mus.get_release_group_image_front(release_id, size=size)

        except mus.NetworkError:
            if retries == 0:
                # raise mus.NetworkError("Failure connecting to MusicBrainz.org")
                return None
            print("warning: Retrying download. {retries} retries left!".format(retires=retries))
            time.sleep(retry_delay)
            self.request_album_art(song, artist, album, size=size, retries=retries - 1)

        except mus.ResponseError:
            print("error: Couldn't find album art for",
                  "{artist} - {album}".format(artist=artist, album=album))
            return None

    def get_default_album_art(self):
        """Return binary version of default album art."""
        return base64.b64decode("""
iVBORw0KGgoAAAANSUhEUgAAAOYAAADmAQMAAAD7pGv4AAAABlBMVEX///8AAABVwtN+AAAChUlE
QVRYw6XZsW0jMRCFYRoXTMYKWIRClsXQ4WXX1lVwNbAQB5YXgiBpZ77gRNiAtZS5/HfJmTePrb3R
Luyb6F1toHe3Xnd+/G1R9/76/fNTtTj+vWr9uHXVxjHtqs3bb4XbALxv965wWw18sJbAcR+gwq2B
x33iFW4NvB5GyHFL4NtsA7glcDwNkeNWwONp6jluBbxexshwC+D7XAO4BXCcBslwc+BxmnyGmwOv
ZJSW3K0DNwV+oEyAIx0mu9kGbgY8i7/P3x/ATYCf5hnATYCjHOh8qw3cM/DEp9dvD+CegF9mGcA9
fQwO1TmNQYRJ/MVHt/XYTy8lml7o04XgUulcZoNLdHJ5L26NrW2VbLpo2rAPl4KhoDOMDIagyfC1
GPq2wmYaVKMpIN8vBkN9Z5oYTDGT6WkxtW2lxSJpRlPCvV0OpvJOGTAoISblx6J02ZI9pSiKJkF1
dASlWqfMG5SIk/JyUZpuyVqI3mgSzNeuoBTvlPGDJYAKhAncH+CN3g7cKzBwr8B/VPB8/GM99MXe
zzd6v/5/Viby0/CT9FvwG/Tb58rxqvOK9Wr3TvEu8w717mZkcFRxRHI0cyR0FHUEdvRm5HfWcMZx
tnKmc5Z0hnV2Zma3KrCisBqxkrEKsoKy+qJys+qzYrTatFK1yrVCtrqmMreqd0XgasKViKsYV0Cu
nlh5uWpzxedq0ZWmq1RXuK6OWVm7KndFbzfAToJdCDsYdj/onNh1sWNjt8dOkV0mO1R2t+iM2VWz
I2c3z06gXUQ7kIvJayvx2TW142q31k6vXWI7zIviZEvY2BW3o2433k6+TwF8grAoPreEq089fGLi
0xaf1PiUxydEF/Re2hvtG6k8p7n4F+LQAAAAAElFTkSuQmCC""")
