import os
import importlib.util
from django.conf import settings


def load_plugins():
    """Load plugins dynamically from the plugins directory."""
    if not settings.ENABLE_PLUGINS:
        return

    plugins_dir = settings.PLUGINS_DIR

    if not os.path.exists(plugins_dir):
        return

    for plugin_name in os.listdir(plugins_dir):
        plugin_path = os.path.join(plugins_dir, plugin_name)

        if os.path.isdir(plugin_path):
            init_file = os.path.join(plugin_path, '__init__.py')

            if os.path.exists(init_file):
                # Correctly form the module name for import
                module_name = f"plugins.{plugin_name}"
                spec = importlib.util.spec_from_file_location(module_name, init_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"Loaded plugin: {module_name}")
