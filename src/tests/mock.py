import stat
from pathlib import Path


def create_mock_module(vault_dir: Path, name: str, config_content: str = "") -> Path:
    """Helper to create a module structure inside mock vault."""
    module_dir: Path = vault_dir / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    if config_content:
        _ = (module_dir / "module_config.toml").write_text(config_content)
    return module_dir


def create_script(module_dir: Path, script_name: str, content: str) -> Path:
    """Helper to create check_installed script."""
    script_dir: Path = module_dir / "check_installed"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path: Path = script_dir / script_name
    _ = script_path.write_text(content)
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path
