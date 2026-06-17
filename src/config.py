"""Configuration management for F1 Strategy Engine."""
import yaml
from pathlib import Path
from typing import Dict, Any


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


def load_training_config() -> Dict[str, Any]:
    """Load training configuration from YAML."""
    config_path = get_project_root() / "config" / "training_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_model_config(model_name: str) -> Dict[str, Any]:
    """
    Load specific model configuration.

    Args:
        model_name: Model identifier (m1, m2, m3, m4, m5)

    Returns:
        Model configuration dictionary
    """
    config_path = get_project_root() / "config" / "model_config.yaml"
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)

    if model_name not in cfg["models"]:
        raise ValueError(f"Model {model_name} not found in config")

    return cfg["models"][model_name]


def load_all_model_configs() -> Dict[str, Dict[str, Any]]:
    """Load all model configurations."""
    config_path = get_project_root() / "config" / "model_config.yaml"
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    return cfg["models"]
