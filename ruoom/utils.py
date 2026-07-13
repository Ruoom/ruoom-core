import os
from django.urls import include, path
import logging
from ruoom.plugin_metadata import get_enabled_plugin_names, get_plugins_dir, load_plugin_metadata

def load_plugin_urls():
    urlpatterns = []

    try:
        for plugin_name in get_enabled_plugin_names():
            try:
                metadata = load_plugin_metadata(plugin_name)
                url_prefix = metadata.url_prefix if metadata else plugin_name + '/'
                url_namespace = metadata.url_namespace if metadata else plugin_name

                # Append the URL patterns with an explicit namespace so {% url 'plugin:view' %} works
                # The included module must define app_name = plugin_name
                urlpatterns += path(
                    url_prefix,
                    include('plugins.' + plugin_name + '.urls', namespace=url_namespace),
                ),
                logging.info(f"Loaded URLs for plugin: {plugin_name}")
            except (ImportError, AttributeError) as e:
                logging.error(f"Error loading URLs for plugin {plugin_name}: {e}")
    except:
        logging.info("No plugins installed")

    return urlpatterns

def load_plugin_statics(BASE_DIR):
    staticfiles_dirs = []
    plugins_dir = get_plugins_dir()
    try:
        for plugin_name in get_enabled_plugin_names():
            plugin_path = plugins_dir + "\\" + plugin_name
            if os.path.isdir(plugin_path+"\\static"):
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

