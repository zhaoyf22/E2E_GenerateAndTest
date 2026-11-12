"""TestForge core services (language-agnostic)."""

from .config import (  # noqa: F401
    DEFAULT_CONFIG,
    DEFAULT_CONFIG_NAME,
    as_dict,
    as_list,
    deep_merge,
    load_config,
    normalize_config_path,
    normalize_stacks,
    project_root,
    stack_root,
)
from .packs import Pack, get_pack, load_pack, load_packs  # noqa: F401
from .detect import DetectedStack, detect_stacks  # noqa: F401
