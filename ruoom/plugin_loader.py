from importlib import import_module

from django.conf import settings

from ruoom.plugin_metadata import get_enabled_plugin_names


def load_plugins():
    """Load plugins dynamically from the plugins directory."""
    if not getattr(settings, "ENABLE_PLUGINS", False):
        return

    for plugin_name in get_enabled_plugin_names():
        module_name = f"plugins.{plugin_name}"
        import_module(module_name)
        print(f"Loaded plugin: {module_name}")
