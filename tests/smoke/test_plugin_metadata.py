from ruoom.plugin_metadata import (
    PluginMetadata,
    PluginSettingsTab,
    get_enabled_plugin_metadata,
    get_enabled_plugin_names,
    get_plugin_navigation_items,
    get_plugin_public_url_patterns,
    get_plugin_settings_tabs,
    get_plugin_staff_only_url_patterns,
    get_plugin_middleware_paths,
    is_plugin_enabled,
    load_plugin_metadata,
)
from ruoom.plugin_loader import load_plugins


def test_booking_plugin_metadata_can_be_loaded():
    metadata = load_plugin_metadata("booking")

    assert isinstance(metadata, PluginMetadata)
    assert metadata.name == "booking"
    assert metadata.app_config == "plugins.booking.apps.BookingConfig"
    assert metadata.url_namespace == "booking"
    assert metadata.url_prefix == "booking/"
    assert metadata.optional_dependencies == ("payment", "customforms")
    assert metadata.export_package_name == "booking-plugin"


def test_unknown_plugin_metadata_returns_none():
    assert load_plugin_metadata("not_a_real_plugin") is None


def test_plugin_presence_helper_requires_explicit_installed_app(monkeypatch, settings):
    settings.ENABLE_PLUGINS = True
    settings.INSTALLED_APPS = []
    monkeypatch.setattr("ruoom.plugin_metadata.os.path.exists", lambda path: True)
    monkeypatch.setattr("ruoom.plugin_metadata.os.listdir", lambda path: ["booking", "disabled"])
    monkeypatch.setattr(
        "ruoom.plugin_metadata.os.path.isdir",
        lambda path: path.endswith("booking") or path.endswith("disabled"),
    )

    assert is_plugin_enabled("booking") is False
    assert get_enabled_plugin_names() == []

    settings.INSTALLED_APPS = ["plugins.booking"]

    assert is_plugin_enabled("booking") is True
    assert get_enabled_plugin_names() == ["booking"]
    assert is_plugin_enabled("payment") is False


def test_plugin_presence_helper_accepts_app_config_install(monkeypatch, settings):
    settings.ENABLE_PLUGINS = True
    settings.INSTALLED_APPS = ["plugins.booking.apps.BookingConfig"]
    monkeypatch.setattr("ruoom.plugin_metadata.os.path.exists", lambda path: True)
    monkeypatch.setattr("ruoom.plugin_metadata.os.path.isdir", lambda path: path.endswith("booking"))

    assert is_plugin_enabled("booking") is True


def test_enabled_plugin_metadata_skips_plugins_without_metadata(monkeypatch, settings):
    settings.ENABLE_PLUGINS = True
    settings.INSTALLED_APPS = ["plugins.booking", "plugins.payment"]
    monkeypatch.setattr("ruoom.plugin_metadata.os.path.exists", lambda path: True)
    monkeypatch.setattr("ruoom.plugin_metadata.os.listdir", lambda path: ["booking", "payment"])
    monkeypatch.setattr("ruoom.plugin_metadata.os.path.isdir", lambda path: True)
    booking_metadata = load_plugin_metadata("booking")
    monkeypatch.setattr(
        "ruoom.plugin_metadata.load_plugin_metadata",
        lambda plugin_name: booking_metadata if plugin_name == "booking" else None,
    )

    metadata = get_enabled_plugin_metadata()

    assert [plugin.name for plugin in metadata] == ["booking"]


def test_plugin_settings_tabs_collect_from_enabled_plugin_metadata():
    settings_tabs = get_plugin_settings_tabs()

    assert PluginSettingsTab(
        label="Payment Processing",
        url_name="payment:settings",
        template_name="payment/partials/settings_nav.html",
        icon_class="fe fe-credit-card",
    ) in settings_tabs
    assert PluginSettingsTab(
        label="Embed Booking Calendar",
        url_name="booking:settings-embed",
        template_name="booking/partials/settings_nav.html",
        icon_class="fe fe-calendar",
    ) in settings_tabs


def test_plugin_navigation_items_collect_from_enabled_plugin_metadata():
    navigation_items = get_plugin_navigation_items()

    assert any(
        item.label == "Forms"
        and item.url_name == "customforms:form_list"
        and item.icon_class == "fe fe-file-text"
        and item.permission_group == "staff"
        for item in navigation_items
    )


def test_plugin_url_contract_helpers_collect_enabled_plugin_patterns():
    public_patterns = get_plugin_public_url_patterns()
    staff_only_patterns = get_plugin_staff_only_url_patterns()

    assert "customforms/webhook/" in public_patterns
    assert "booking/settings/" in staff_only_patterns


def test_plugin_middleware_contract_helpers_collect_enabled_plugin_paths():
    middleware_paths = get_plugin_middleware_paths()

    assert "plugins.single_sign_on.middleware.sso.SSOMiddleware" in middleware_paths


def test_load_plugin_metadata_raises_for_broken_import(monkeypatch):
    def broken_import(module_name):
        raise ModuleNotFoundError("missing dependency", name="missing_dependency")

    monkeypatch.setattr("ruoom.plugin_metadata.import_module", broken_import)

    try:
        load_plugin_metadata("booking")
        assert False, "Expected ModuleNotFoundError"
    except ModuleNotFoundError as exc:
        assert exc.name == "missing_dependency"


def test_plugin_loader_imports_enabled_plugin_modules(monkeypatch, settings):
    imported_modules = []

    settings.ENABLE_PLUGINS = True
    monkeypatch.setattr("ruoom.plugin_loader.get_enabled_plugin_names", lambda: ["booking"])
    monkeypatch.setattr(
        "ruoom.plugin_loader.import_module",
        lambda module_name: imported_modules.append(module_name),
    )

    load_plugins()

    assert imported_modules == ["plugins.booking"]
