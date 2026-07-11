from typing import Any

import yaml
from yaml import SafeLoader

SAFE_LOADER: type[SafeLoader] = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def yaml_safe_load(stream: Any) -> Any:
    """
    Optimized YAML safe loader that uses CSafeLoader if available,
    falling back to standard SafeLoader.
    """
    return yaml.load(stream, Loader=SAFE_LOADER)
