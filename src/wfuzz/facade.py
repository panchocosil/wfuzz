from . import utils
from . import __version__ as version
from .externals.moduleman.registrant import MulRegistrant
from .externals.moduleman.loader import DirLoader
from .externals.settings.settings import SettingsBase
from .exception import FuzzExceptNoPluginError, FuzzExceptPluginLoadError

import os


class Settings(SettingsBase):
    def get_config_file(self):
        return os.path.join(utils.get_home(check=True), "wfuzz.ini")

    def set_defaults(self):
        return dict(
            plugins=[("bing_apikey", '')],
            kbase=[("discovery.blacklist", '.svg-.css-.js-.jpg-.gif-.png-.jpeg-.mov-.avi-.flv-.ico')],
            connection=[
                ("concurrent", '10'),
                ("conn_delay", '90'),
                ("req_delay", '90'),
                ("retries", '3'),
                ("User-Agent", "Wfuzz/%s" % version)
            ],
            general=[
                ("default_printer", 'raw'),
                ("cancel_on_plugin_except", "1"),
                ("concurrent_plugins", '3'),
                ("lookup_dirs", '.'),
                ("encode_space", '1')
            ],
        )


class MyRegistrant(MulRegistrant):
    def get_plugin(self, identifier):
        try:
            return MulRegistrant.get_plugin(self, identifier)
        except KeyError, e:
            raise FuzzExceptNoPluginError("Requested plugin %s. Error: %s" % (identifier, str(e)))


class Facade:
    __metaclass__ = utils.Singleton

    def __init__(self):

        self.__plugins = dict(
            printers=None,
            scripts=None,
            encoders=None,
            iterators=None,
            payloads=None,
        )

        self.sett = Settings()

    def _load(self, cat):
        try:
            if cat not in self.__plugins:
                raise FuzzExceptNoPluginError("Non-existent plugin category %s" % cat)

            if not self.__plugins[cat]:
                loader_list = []
                loader_list.append(DirLoader(**{"base_dir": cat, "base_path": utils.get_path("plugins")}))
                loader_list.append(DirLoader(**{"base_dir": cat, "base_path": utils.get_home()}))
                self.__plugins[cat] = MyRegistrant(loader_list)

            return self.__plugins[cat]
        except Exception, e:
            raise FuzzExceptPluginLoadError("Error loading plugins: %s" % str(e))

    def proxy(self, which):
        return self._load(which)

    def __getattr__(self, name):
        if name in ["printers", "payloads", "iterators", "encoders", "scripts"]:
            return self._load(name)
        else:
            raise AttributeError
