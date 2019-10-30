from __future__ import unicode_literals

import logging
import os
from pkg_resources import iter_entry_points

from mopidy import config, ext


__version__ = "0.0.1"

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = "Mopidy-PiDi"
    ext_name = "pidi"
    version = __version__

    @classmethod
    def get_display_types(self):
        display_types = {}
        for entry_point in iter_entry_points("pidi.plugin.display"):
            try:
                plugin = entry_point.load()
                display_types[plugin.option_name] = plugin
            except (ImportError) as err:
                logger.log(logging.WARN, "Error loading display plugin {entry_point}: {err}".format(
                    entry_point=entry_point,
                    err=err))

        return display_types

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), "ext.conf")
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema["display"] = config.String(choices=self.get_display_types().keys())
        return schema

    def setup(self, registry):
        from .frontend import PiDiFrontend
        registry.add("frontend", PiDiFrontend)
