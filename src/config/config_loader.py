import yaml
from functools import lru_cache


@lru_cache(maxsize=1)
def load_config():
    with open("src/config/config.yaml") as f:
        return yaml.safe_load(f)
