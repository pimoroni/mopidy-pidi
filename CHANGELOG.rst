*********
Changelog
*********

v1.0.4
========================================

- Add idle timeout support

v1.0.3
========================================

- Add support for display rotation
- Implement "stream_title_changed" to update display upon radio track change

v1.0.2
========================================

- Add support for stopping display plugins on exit.

v1.0.1
========================================

- BugFix: support for mopidy-youtube, handle None Image.width/Image.height
- BugFix: support for mopidy-tunein, handle None Track.length
- BugFix: cache filename bug caused by Base64 outputting /

v1.0.0
========================================

- Breaking release!
- Dropped support for Python 2.x and Mopidy 2.x
- Support for Mopidy 3.x+, Python 3.x

v0.2.0
========================================

- Use Mopidy supplied album art where available, only use Brainz as a fallback
- Attempt to discover and display public IP address on start
- BugFix: display current volume on start


v0.1.0
========================================

- Threaded album art retrival to avoid locking up frontend
- BugFix: fixed typo in album art retry functionality
- BugFix: use time.sleep instead of event.wait, which was returning immediately


v0.0.2
========================================

- Depend upon musicbrainzngs


v0.0.1
========================================

- Initial release.
