*********
Changelog
*********

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
