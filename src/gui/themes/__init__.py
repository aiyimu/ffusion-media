from pathlib import Path


def get_dark_theme() -> str:
    theme_path = Path(__file__).parent / "dark_theme.qss"
    if theme_path.exists():
        with open(theme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def get_light_theme() -> str:
    theme_path = Path(__file__).parent / "light_theme.qss"
    if theme_path.exists():
        with open(theme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


__all__ = ["get_dark_theme", "get_light_theme"]
