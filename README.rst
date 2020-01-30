****************************
Mopidy-PiDi
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-PiDi.svg
    :target: https://pypi.org/project/Mopidy-PiDi/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/circleci/build/gh/pimoroni/mopidy-pidi/master.svg
    :target: https://circleci.com/gh/pimoroni/mopidy-pidi
    :alt: Travis CI build status

.. image:: https://img.shields.io/codecov/gh/pimoroni/mopidy-pidi/master.svg
   :target: https://codecov.io/gh/pimoroni/mopidy-pidi
   :alt: Test coverage

Mopidy extension for displaying song info and album art using pidi display plugins.


Installation
============

Install by running::

    pip3 install Mopidy-PiDi

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<https://apt.mopidy.com/>`_.

You must then install a display plugin, for example::

    pip3 install pidi-display-st7789


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-PiDi to your Mopidy configuration file::

    [pidi]
    enabled = true
    display = st7789

This example uses st7789 provided by pidi-display-st7789


Project resources
=================

- `Source code <https://github.com/pimoroni/mopidy-pidi>`_
- `Issue tracker <https://github.com/pimoroni/mopidy-pidi/issues>`_
- `Changelog <https://github.com/pimoroni/mopidy-pidi/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `Phil Howard <https://github.com/pimoroni>`__
- Current maintainer: `Phil Howard <https://github.com/pimoroni>`__
- `Contributors <https://github.com/pimoroni/mopidy-pidi/graphs/contributors>`_
