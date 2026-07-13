from dataclasses import dataclass, field
from importlib import import_module
import os
from typing import List, Optional, Tuple

from django.apps import apps
from django.conf import settings


@dataclass(frozen=True)
class PluginNavigationItem:
    label: str
    url_name: str
    icon_class: str = ""
    permission_group: str = "staff"


@dataclass(frozen=True)
class PluginSettingsTab:
    label: str
    url_name: str
    template_name: str
    icon_class: str = ""


@dataclass(frozen=True)
class PluginMetadata:
    name: str
    app_config: str
    url_namespace: str
    url_prefix: str
    permission_groups: Tuple[str, ...] = field(default_factory=tuple)
    navigation_items: Tuple[PluginNavigationItem, ...] = field(default_factory=tuple)
    settings_tabs: Tuple[PluginSettingsTab, ...] = field(default_factory=tuple)
    public_url_patterns: Tuple[str, ...] = field(default_factory=tuple)
    staff_only_url_patterns: Tuple[str, ...] = field(default_factory=tuple)
    middleware: Tuple[str, ...] = field(default_factory=tuple)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    optional_dependencies: Tuple[str, ...] = field(default_factory=tuple)
    export_package_name: Optional[str] = None
    package_version: Optional[str] = None
    repository_url: Optional[str] = None
    test_command: Optional[str] = None


def load_plugin_metadata(plugin_name: str) -> Optional[PluginMetadata]:
    package_name = "plugins.%s" % plugin_name
    module_name = f"plugins.{plugin_name}.plugin"
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name in (package_name, module_name):
            return None
        raise

    metadata = getattr(module, "PLUGIN_METADATA", None)
    if metadata is None:
        return None

    if not isinstance(metadata, PluginMetadata):
        raise TypeError(
            f"plugins.{plugin_name}.plugin.PLUGIN_METADATA must be a PluginMetadata instance."
        )

    return metadata


def get_plugins_dir() -> str:
    return getattr(
        settings,
        "PLUGINS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),
    )


def get_enabled_plugin_names() -> List[str]:
    if not getattr(settings, "ENABLE_PLUGINS", False):
        return []

    configured_names = getattr(settings, "RUOOM_PLUGIN_NAMES", ())
    return [name for name in configured_names if is_plugin_enabled(name)]


def is_plugin_enabled(plugin_name: str) -> bool:
    if not getattr(settings, "ENABLE_PLUGINS", False):
        return False

    return apps.is_installed(f"plugins.{plugin_name}")


def get_enabled_plugin_metadata() -> List[PluginMetadata]:
    metadata_list = []
    for plugin_name in get_enabled_plugin_names():
        metadata = load_plugin_metadata(plugin_name)
        if metadata is not None:
            metadata_list.append(metadata)
    return metadata_list


def get_plugin_settings_tabs() -> List[PluginSettingsTab]:
    settings_tabs = []
    for metadata in get_enabled_plugin_metadata():
        settings_tabs.extend(metadata.settings_tabs)
    return settings_tabs


def get_plugin_navigation_items() -> List[PluginNavigationItem]:
    navigation_items = []
    for metadata in get_enabled_plugin_metadata():
        navigation_items.extend(metadata.navigation_items)
    return navigation_items


def get_plugin_permission_groups() -> Tuple[str, ...]:
    permission_groups = []
    for metadata in get_enabled_plugin_metadata():
        permission_groups.extend(metadata.permission_groups)
        permission_groups.extend(
            item.permission_group for item in metadata.navigation_items
        )
    return tuple(dict.fromkeys(permission_groups))


def get_plugin_public_url_patterns() -> Tuple[str, ...]:
    patterns = []
    for metadata in get_enabled_plugin_metadata():
        patterns.extend(metadata.public_url_patterns)
    return tuple(patterns)


def get_plugin_staff_only_url_patterns() -> Tuple[str, ...]:
    patterns = []
    for metadata in get_enabled_plugin_metadata():
        patterns.extend(metadata.staff_only_url_patterns)
    return tuple(patterns)


def get_plugin_middleware_paths() -> Tuple[str, ...]:
    middleware_paths = []
    for metadata in get_enabled_plugin_metadata():
        middleware_paths.extend(metadata.middleware)
    return tuple(middleware_paths)
