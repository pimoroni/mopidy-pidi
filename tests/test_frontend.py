import pkg_resources
import pykka
from mopidy import core

import pytest
from mopidy_pidi import frontend as frontend_lib

from . import dummy_audio, dummy_backend, dummy_mixer


def stop_mopidy_core():
    pykka.ActorRegistry.stop_all()


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    request.addfinalizer(stop_mopidy_core)


@pytest.fixture
def frontend():
    mixer = dummy_mixer.create_proxy()
    audio = dummy_audio.create_proxy()
    backend = dummy_backend.create_proxy(audio=audio)
    dummy_core = core.Core.start(audio=audio, mixer=mixer, backends=[backend]).proxy()

    distribution = pkg_resources.Distribution(__file__)
    endpoint = pkg_resources.EntryPoint.parse(
        "dummy = mopidy_pidi.plugin:DisplayDummy", dist=distribution
    )
    distribution._ep_map = {"pidi.plugin.display": {"dummy": endpoint}}
    pkg_resources.working_set.add(distribution, "dummy")

    config = {"pidi": {"display": "dummy"}, "core": {"data_dir": "/tmp"}}

    return frontend_lib.PiDiFrontend(config, dummy_core)


def test_on_start(frontend):
    frontend.on_start()
    frontend.on_stop()


def test_options_changed(frontend):
    frontend.on_start()
    frontend.options_changed()
    frontend.on_stop()
