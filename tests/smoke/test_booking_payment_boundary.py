from decimal import Decimal

import pytest
from django.test import Client, override_settings

from plugins.booking.models import CustomerCheckin
from plugins.booking.payment_boundary import (
    PAYMENT_UNAVAILABLE_MESSAGE,
    add_store_item_to_cart,
    get_business_refund_policy,
    payment_checkout_is_configured,
    refund_service_checkin_orders,
    refund_service_order,
)
from plugins.payment.models import Cart, Order
from plugins.booking.payment_boundary import build_booking_payment_context
from ruoom.plugin_metadata import is_plugin_enabled
from tests.factories import (
    create_business,
    create_cart,
    create_location,
    create_payment_settings,
    create_profile,
    create_service,
)


@pytest.mark.django_db
def test_build_booking_payment_context_returns_neutral_values_when_payment_disabled(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]
    business = create_business()
    user = create_profile(business_id=business.business_id)

    context = build_booking_payment_context(business_id=business.business_id, user=user)

    assert is_plugin_enabled("payment") is False
    assert context.enabled is False
    assert context.checkout_url is None
    assert context.total_price == Decimal("0.00")
    assert context.refund_policy == ""


@pytest.mark.django_db
def test_refund_service_checkin_orders_returns_unavailable_when_payment_disabled(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]
    business = create_business()
    customer = create_profile(business_id=business.business_id)

    result = refund_service_checkin_orders(
        business_id=business.business_id,
        customer=customer,
        service_id=12345,
    )

    assert result == (False, PAYMENT_UNAVAILABLE_MESSAGE)


@pytest.mark.django_db
def test_build_booking_payment_context_returns_checkout_data_when_payment_enabled():
    business = create_business()
    location = create_location(business_id=business.business_id)
    service = create_service(location=location, business_id=business.business_id)
    user = create_profile(email="buyer@example.com", business_id=business.business_id, default_location=location)
    create_payment_settings(business=business, refund_policy="48 hour policy", refund_popup=True)
    create_cart(customer=user, service=service, location=location, business_id=business.business_id)

    context = build_booking_payment_context(business_id=business.business_id, user=user)

    assert context.enabled is True
    assert context.checkout_url == "/payment/checkout/customer"
    assert context.total_price == Decimal("25.00")
    assert context.refund_policy == "48 hour policy"
    assert context.refund_popup is True


@pytest.mark.django_db
def test_add_store_item_to_cart_returns_unavailable_when_payment_disabled(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]
    business = create_business()
    customer = create_profile(business_id=business.business_id)

    result = add_store_item_to_cart(
        business_id=business.business_id,
        customer=customer,
        store_type="digital_good",
        product_id="sku-1",
    )

    assert result == (False, PAYMENT_UNAVAILABLE_MESSAGE)


@pytest.mark.django_db
def test_add_store_item_to_cart_creates_cart_when_payment_enabled():
    business = create_business()
    customer = create_profile(business_id=business.business_id)

    ok, cart = add_store_item_to_cart(
        business_id=business.business_id,
        customer=customer,
        store_type="digital_good",
        product_id="sku-1",
        product_quantity=2,
    )

    assert ok is True
    assert cart.item_type == "digital_good"
    assert cart.product_id == "sku-1"
    assert cart.product_quantity == 2


@pytest.mark.django_db
def test_booking_calendar_view_renders_with_payment_enabled():
    business = create_business(name="Booking And Payment Business")
    location = create_location(business_id=business.business_id)
    service = create_service(location=location, business_id=business.business_id)
    user = create_profile(email="calendar@example.com", business_id=business.business_id, default_location=location)
    create_payment_settings(business=business, refund_policy="Calendar refund policy", refund_popup=True)
    create_cart(customer=user, service=service, location=location, business_id=business.business_id)
    client = Client()
    client.force_login(user)

    response = client.get("/booking/calendar/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context["payment_enabled"] is True
    assert response.context["payment_checkout_url"] == "/payment/checkout/customer"
    assert response.context["total_price"] == Decimal("25.00")
    assert response.context["refund_policy"] == "Calendar refund policy"


@pytest.mark.django_db
def test_refund_service_order_returns_unavailable_when_payment_disabled(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]

    result = refund_service_order(business_id=1, order_id=123)

    assert result == (False, PAYMENT_UNAVAILABLE_MESSAGE)


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_ajax_add_booking_cart_creates_payment_cart_when_enabled():
    business = create_business()
    location = create_location(business_id=business.business_id)
    service = create_service(location=location, business_id=business.business_id, capacity=5)
    user = create_profile(email="cart@example.com", business_id=business.business_id, default_location=location)
    create_payment_settings(business=business)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/booking/ajax/add_booking_cart/",
        {
            "class_id": service.id,
            "customer_id": user.id,
            "id_in_layout": "",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json()["message"] == "success"
    assert Cart.objects.filter(customer=user, product_id=str(service.id)).count() == 1


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_customer_checkin_cancel_and_refund_returns_unavailable_when_payment_disabled(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]
    business = create_business()
    service = create_service(business_id=business.business_id)
    customer = create_profile(email="refund-disabled@example.com", business_id=business.business_id)
    checkin = CustomerCheckin.objects.create(customer=customer, in_class=service, waitlist=False, present=False, cancelled=False, paid=True)

    result = checkin.cancel_and_refund()

    checkin.refresh_from_db()
    assert checkin.cancelled is True
    assert result == (False, PAYMENT_UNAVAILABLE_MESSAGE)


@pytest.mark.django_db
def test_customer_checkin_refund_uses_matching_payment_order(monkeypatch):
    business = create_business()
    service = create_service(business_id=business.business_id)
    customer = create_profile(email="refund-enabled@example.com", business_id=business.business_id)
    other_customer = create_profile(email="other-refund@example.com", business_id=business.business_id)
    checkin = CustomerCheckin.objects.create(customer=customer, in_class=service, waitlist=False, present=False, cancelled=False, paid=True)
    matching_order = Order.objects.create(
        customer=customer,
        product_type="service_register",
        business_id=business.business_id,
        product_id=str(service.id),
    )
    Order.objects.create(
        customer=other_customer,
        product_type="service_register",
        business_id=business.business_id,
        product_id=str(service.id),
    )
    calls = []

    def fake_payment_refund(business_id, **kwargs):
        calls.append((business_id, kwargs))
        return True, "Refunded"

    monkeypatch.setattr("plugins.payment.helpers.payment_refund", fake_payment_refund)

    result = checkin.refund(late_cancelled=False)

    assert result == (True, "Refunded")
    assert calls == [
        (
            business.business_id,
            {
                "order_id": matching_order.id,
                "percent_enabled": False,
                "refund_pct": 100,
                "flatfee_enabled": False,
                "flatfee": 0,
                "flatcredits_enabled": False,
                "flatcredits": 0,
            },
        )
    ]


@pytest.mark.django_db
def test_customer_checkin_late_refund_uses_business_noshow_percent_policy(monkeypatch):
    business = create_business(
        noshow_options_prepay="noshow_prepay_percent",
        noshow_prepay_percentfee=50,
    )
    service = create_service(business_id=business.business_id)
    customer = create_profile(email="late-refund@example.com", business_id=business.business_id)
    checkin = CustomerCheckin.objects.create(customer=customer, in_class=service, waitlist=False, present=False, cancelled=False, paid=True)
    matching_order = Order.objects.create(
        customer=customer,
        product_type="service_register",
        business_id=business.business_id,
        product_id=str(service.id),
    )
    calls = []

    def fake_payment_refund(business_id, **kwargs):
        calls.append((business_id, kwargs))
        return True, "Refunded"

    monkeypatch.setattr("plugins.payment.helpers.payment_refund", fake_payment_refund)

    result = checkin.refund(late_cancelled=True)

    assert result == (True, "Refunded")
    assert calls == [
        (
            business.business_id,
            {
                "order_id": matching_order.id,
                "percent_enabled": True,
                "refund_pct": 50,
                "flatfee_enabled": False,
                "flatfee": 0,
                "flatcredits_enabled": False,
                "flatcredits": 0,
            },
        )
    ]


@pytest.mark.django_db
def test_unpaid_noshow_charge_policy_returns_unavailable_without_charge_method():
    business = create_business(
        noshow_options_notprepay="noshow_notprepay_flat",
        noshow_notprepay_flatfee=10,
    )
    service = create_service(business_id=business.business_id)
    customer = create_profile(email="unpaid-noshow@example.com", business_id=business.business_id)
    checkin = CustomerCheckin.objects.create(customer=customer, in_class=service, waitlist=False, present=False, cancelled=False, paid=False)

    result = checkin.cancel_noshow()

    checkin.refresh_from_db()
    assert checkin.cancelled is True
    assert checkin.no_show is True
    assert result == (False, "No payment found and automatic no-show charging is not configured.")


@pytest.mark.django_db
def test_get_business_refund_policy_returns_empty_string_without_settings():
    assert get_business_refund_policy(business_id=9999) == ""


@pytest.mark.django_db
def test_payment_checkout_is_configured_handles_supported_gateways():
    business = create_business()

    assert payment_checkout_is_configured(business.business_id) is False

    stripe = create_payment_settings(
        business=business,
        payment_gateway_type="stripe",
        stripe_api_key="sk_test",
        stripe_publishable_key="pk_test",
    )
    assert payment_checkout_is_configured(business.business_id) is True

    stripe.stripe_publishable_key = ""
    stripe.save(update_fields=["stripe_publishable_key"])
    assert payment_checkout_is_configured(business.business_id) is False

    stripe.payment_gateway_type = "paypal"
    stripe.paypal_client_id_key = "client"
    stripe.paypal_secret_key = "secret"
    stripe.paypal_merchant_id = "merchant"
    stripe.save(
        update_fields=[
            "payment_gateway_type",
            "paypal_client_id_key",
            "paypal_secret_key",
            "paypal_merchant_id",
        ]
    )
    assert payment_checkout_is_configured(business.business_id) is True

    stripe.paypal_secret_key = ""
    stripe.save(update_fields=["paypal_secret_key"])
    assert payment_checkout_is_configured(business.business_id) is False

    stripe.payment_gateway_type = "iamport"
    stripe.iamport_id = "iamport-id"
    stripe.iamport_secret = "iamport-secret"
    stripe.iamport_merchant = "iamport-merchant"
    stripe.save(
        update_fields=[
            "payment_gateway_type",
            "iamport_id",
            "iamport_secret",
            "iamport_merchant",
        ]
    )
    assert payment_checkout_is_configured(business.business_id) is True
