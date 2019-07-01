# core
import configparser
import logging
import os

# non-core
from xdg import XDG_CONFIG_HOME
import getpass

# local
from cathsm.apiclient.errors import ConfigError

LOG = logging.getLogger(__name__)
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'cath-swissmodel-api')
os.makedirs(CONFIG_DIR, exist_ok=True)
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")


class ApiConfig(object):
    """
    Defines API configuration file (saves API token)
    """

    def __init__(self, *, section='DEFAULT', filename=DEFAULT_CONFIG_FILE):
        """Creates a new instance of config file from a JSON filehandle."""
        self.filename = filename
        self.section = str(section)

        self._config = configparser.ConfigParser()

        if os.path.isfile(filename):
            self._config.read(filename)
            LOG.info("Loaded config from {}".format(filename))

        if self.section not in self._config:
            self._config[self.section] = {}

    def delete_section(self, *, section_id=None):
        """Removes all keys that match the given section."""
        if not section_id:
            section_id = self.section
        if section_id in self._config:
            del(self._config[section_id])
        self.write()

    def __contains__(self, key):
        section = self._config[self.section] if self.section in self._config else {
        }
        return key in section

    def __getitem__(self, key):
        key = str(key)
        section = self._config[self.section]
        LOG.debug("__getitem__: {}, {} (type:{})".format(
            self.section, key, type(key)))
        return section[key]

    def __setitem__(self, key, value):
        if self.section not in self._config:
            self._config[self.section] = {}
        section = self._config[self.section]
        section[key] = value
        LOG.debug("Set config [{}] {}={}".format(self.section, key, value))
        self.write()

    def write(self):
        with open(self.filename, 'w') as outfile:
            self._config.write(outfile)
        LOG.debug("Saved config to {}".format(self.filename))

    def as_dict(self):
        d = dict(self._config[self.section])
        return d
