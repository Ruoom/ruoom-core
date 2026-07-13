from ruoom.plugin_metadata import PluginMetadata
from ruoom.utils import load_plugin_urls


def test_plugin_urls_include_expected_enabled_plugins():
    route_patterns = load_plugin_urls()
    route_strings = sorted(str(pattern.pattern) for pattern in route_patterns)

    assert "appointments/" in route_strings
    assert "booking/" in route_strings
    assert "customforms/" in route_strings
    assert "digitalproducts/" in route_strings
    assert "mailerlite/" in route_strings
    assert "otp/" in route_strings
    assert "payment/" in route_strings
    assert "sso/" in route_strings


def test_plugin_urls_skip_disabled_directory():
    route_patterns = load_plugin_urls()
    route_strings = [str(pattern.pattern) for pattern in route_patterns]

    assert "disabled/" not in route_strings


def test_plugin_urls_use_metadata_for_plugin_prefix(monkeypatch):
    monkeypatch.setattr("ruoom.utils.get_enabled_plugin_names", lambda: ["booking"])
    monkeypatch.setattr(
        "ruoom.utils.load_plugin_metadata",
        lambda plugin_name: PluginMetadata(
            name=plugin_name,
            app_config="plugins.booking.apps.BookingConfig",
            url_namespace="booking",
            url_prefix="classes/",
        ),
    )

    route_patterns = load_plugin_urls()
    route_strings = [str(pattern.pattern) for pattern in route_patterns]

    assert route_strings == ["classes/"]
