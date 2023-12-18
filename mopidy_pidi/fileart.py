import os
import eyed3
import mpd
import urllib.parse
import base64
from mopidy import config

class Fileart:
    def __init__(self, cache_dir,directory_path):
        self._cache_dir = cache_dir
        self._default_filename = os.path.join(self._cache_dir, "__default.jpg")
        album_art_data = self.get_default_album_art()
        self.directory_path = directory_path
        self.save_album_art(self.get_default_album_art(), self._default_filename)

    def save_album_art(self, album_art_data, file_path):
        if album_art_data is not None:
            with open(file_path, 'wb') as f:
                f.write(album_art_data)


    def extract_album_art(self, file_path):
        try:
            # Load MP3 tags and print all frames
            audiofile = eyed3.load(file_path)
            frames = audiofile.tag.frame_set
            for frame_id, frame in frames.items():
                # Check for the 'APIC' frame using bytes format
                if b'APIC' in frames:
                    # Get the album art data from the 'APIC' frame
                    album_art_data = frames[b'APIC'][0].image_data

                    # Save album art to a file named "album.jpg"
                    with open(os.path.join(self._cache_dir, "album.jpg"), 'wb') as f:
                        f.write(album_art_data)
                else:
                    # Save default album art to "album.jpg"
                    default_art_data = self.get_default_album_art()
                    with open(os.path.join(self._cache_dir, "album.jpg"), 'wb') as f:
                        f.write(default_art_data)
        except Exception as e:
            print(f'Error: {e}')


    def get_current_playing_file(self):
        try:
            client = mpd.MPDClient()
            client.connect("localhost", 6600)
            current_song = client.currentsong()
            if 'file' in current_song:
                # Decode percent-encoded path and replace 'local:track:' with the actual directory path
                mpd_file_path = urllib.parse.unquote_plus(current_song['file'])
                print('directory_path',self.directory_path)
                mpd_file_path = mpd_file_path.replace('local:track:', self.directory_path + '/')
                return mpd_file_path
            else:
                return None
        except Exception as e:
            print(f'Error getting current playing file: {e}')
            return None
        finally:
            client.close()
            client.disconnect()
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
