from typing import Any
import yaml

SafeLoader: type = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def yaml_safe_load(stream: Any) -> Any:
    """
    Optimized YAML safe loader that uses CSafeLoader if available,
    falling back to standard SafeLoader.
    """
    return yaml.load(stream, Loader=SafeLoader)
