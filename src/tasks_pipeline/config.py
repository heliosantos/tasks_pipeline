import yaml


config = None


def load_config(path):
    global config
    with open(path, 'rb') as f:
        config = yaml.safe_load(f.read().decode('utf-8'))
    return config


def get_config():
    global config
    return config
