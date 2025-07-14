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
                    # Append the URL patterns
                    urlpatterns += path(plugin_name + '/', include('plugins.' + plugin_name + '.urls'), name=plugin_name),              
                    logging.info(f"Loaded URLs for plugin: {plugin_name}")
                except (ImportError, AttributeError) as e:
                    logging.error(f"Error loading URLs for plugin {plugin_name}: {e}")
    except:
        logging.info("No plugins installed")

    return urlpatterns

def load_plugin_statics(BASE_DIR):
    staticfiles_dirs = []
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')
    try:
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            if os.path.isdir(plugin_path+"\\static") and plugin_name != 'disabled':
                try:
                    # Append the static files directory
                    staticfiles_dirs.append(os.path.join(BASE_DIR, plugin_path+"\\static"))
                    logging.info(f"Loaded static files for plugin: {plugin_name}")
                except (ImportError, AttributeError) as e:
                    logging.error(f"Error loading static files for plugin {plugin_name}: {e}")
    except:
        logging.info("No plugins installed")
        print("No plugins installed")

    return staticfiles_dirs
            