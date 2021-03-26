import os
import yaml
import logging.config


def setup_logging(
        default_path='logging.yaml',
        default_level=logging.INFO,
        config_env_key='LOGGING_YAML_CONFIG'):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.environ.get(config_env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
