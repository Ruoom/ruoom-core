import os
import importlib
from django.urls import include, path
import logging

def load_plugin_urls():
    urlpatterns = []
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')

    try:
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            if os.path.isdir(plugin_path) and plugin_name != 'disabled':
                try:
                    # Dynamically import the urls module
                    urls_module = importlib.import_module(f'plugins.{plugin_name}.urls')
                    # Append the URL patterns
                    urlpatterns += path(plugin_name + '/', include('plugins.' + plugin_name + '.urls'), name=plugin_name),              
                    logging.info(f"Loaded URLs for plugin: {plugin_name}")
                except (ImportError, AttributeError) as e:
                    logging.error(f"Error loading URLs for plugin {plugin_name}: {e}")
    except:
        logging.info("No plugins installed")

    return urlpatterns
