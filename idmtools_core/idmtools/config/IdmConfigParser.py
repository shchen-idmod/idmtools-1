import copy
import os
from configparser import ConfigParser

default_config = 'idmtools.ini'


class IdmConfigParser:
    _config = None
    _instance = None
    _config_path = None

    def __new__(cls, dir_path='.', file_name=default_config):
        if not cls._instance:
            cls._instance = super(IdmConfigParser, cls).__new__(cls)
            cls._instance._load_config_file(dir_path, file_name)
        return cls._instance

    @classmethod
    def retrieve_settings(cls, section=None, field_type={}):
        import ast

        cls.ensure_init()

        # retrieve THIS platform config settings
        field_config = cls._get_section(section)

        # update field types
        field_config_updated = copy.deepcopy(field_config)
        fs = set(field_type.keys()).intersection(set(field_config.keys()))

        for fn in fs:
            ft = field_type[fn]
            if ft in [int, float, str]:
                field_config_updated[fn] = ft(field_config[fn])
            elif ft is bool:
                field_config_updated[fn] = ast.literal_eval(field_config[fn])
            else:
                pass

        return field_config_updated

    @classmethod
    def _find_config(cls, dir_path, file_name=default_config):
        full_dir_path = os.path.abspath(dir_path)
        if os.path.exists(os.path.join(full_dir_path, file_name)):
            cls._config_path = os.path.join(full_dir_path, file_name)
            return cls._config_path
        else:
            dir_parent = os.path.dirname(full_dir_path)
            if dir_parent == full_dir_path:
                return None
            else:
                cls._config_path = cls._find_config(dir_parent, file_name)
                return cls._config_path

    @classmethod
    def _load_config_file(cls, dir_path='.', file_name=default_config):
        ini_file = cls._find_config(dir_path, file_name)
        if ini_file is None:
            print("/!\\ WARNING: File '{}' Not Found!".format(file_name))
            return

        print("INI File Used: {}\n".format(ini_file))

        cls._config = ConfigParser()
        cls._config.read(ini_file)

    @classmethod
    def _get_section(cls, section=None):
        cls.ensure_init()
        if cls._config is None:
            return {}

        section = cls._config.items(section)
        return dict(section)

    @classmethod
    def get_config_path(cls):
        cls.ensure_init()
        return cls._config_path

    @classmethod
    def display_config_path(cls) -> object:
        cls.ensure_init()
        print(cls.get_config_path())

    @classmethod
    def view_config_file(cls):
        cls.ensure_init()
        print("View Config INI: \n{}".format(cls._config_path))
        print('-' * len(cls._config_path), '\n')
        with open(cls._config_path) as f:
            read_data = f.read()
            print(read_data)

    @classmethod
    def get_option(cls, section, option):
        cls.ensure_init()
        return cls._config.get(section.upper(), option)

    @classmethod
    def ensure_init(cls, dir_path='.', file_name=default_config):
        if cls._instance is None:
            cls(dir_path, file_name)
