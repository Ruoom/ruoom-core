from django.test import TestCase
from .models import *
from store.models import *
from registration.models import *
from django.test.client import Client

# Create your tests here.


class DigitalGood(TestCase):
   
    def CheckoutDigital(self,id=1):
        layout = ClassBookingCart.objects.get(id=id)
        response = self.c.get('/customer/payment')
        data = {"request": {
                    "method": "POST",
                    "url": "https://beta0.us.ruoomplatform.com/customer/add-new-card/",
                    "httpVersion": "",
                    "headers": [
                        {
                        "name": "sec-ch-ua",
                        "value": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"101\", \"Google Chrome\";v=\"101\""
                        },
                        {
                        "name": "sec-ch-ua-mobile",
                        "value": "?0"
                        },
                        {
                        "name": "User-Agent",
                        "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36"
                        },
                        {
                        "name": "Content-Type",
                        "value": "application/x-www-form-urlencoded; charset=UTF-8"
                        },
                        {
                        "name": "Accept",
                        "value": "*/*"
                        },
                        {
                        "name": "Referer",
                        "value": "https://beta0.us.ruoomplatform.com/customer/checkout/digitalgood/1/norefresh"
                        },
                        {
                        "name": "X-Requested-With",
                        "value": "XMLHttpRequest"
                        },
                        {
                        "name": "sec-ch-ua-platform",
                        "value": "\"Windows\""
                        }
                    ],
                    "queryString": [],
                    "cookies": [],
                    "headersSize": -1,
                    "bodySize": 420,
                    "postData": {
                        "mimeType": "application/x-www-form-urlencoded; charset=UTF-8",
                        "text": "csrfmiddlewaretoken=3E4o9CI9k3cdcIPJ6JypcFqGpWRwpaFMI8ntYhvE9yI7G02IV5IPg2xMc1Nl4Grk&customer=15&guest_cart_id=&new_customer_name=Kevin+M&new_custome_email=kevin%40ruoomsoftware.com&gratuity_amount=1&amount=11&payment_method=paypal_button&customer_purchasing=15&default_card=&order_id=137&number=&allow_account_balance=false&allow_credit_balance=false&sales_tax=0&additional_tax=0&paypal_transaction_id=0PW75387XC778912A",
                        "params": [
                        {
                            "name": "csrfmiddlewaretoken",
                            "value": "3E4o9CI9k3cdcIPJ6JypcFqGpWRwpaFMI8ntYhvE9yI7G02IV5IPg2xMc1Nl4Grk"
                        },
                        {
                            "name": "customer",
                            "value": "15"
                        },
                        {
                            "name": "guest_cart_id",
                            "value": ""
                        },
                        {
                            "name": "new_customer_name",
                            "value": "Kevin+M"
                        },
                        {
                            "name": "new_custome_email",
                            "value": "kevin%40ruoomsoftware.com"
                        },
                        {
                            "name": "gratuity_amount",
                            "value": "1"
                        },
                        {
                            "name": "amount",
                            "value": "11"
                        },
                        {
                            "name": "payment_method",
                            "value": "paypal_button"
                        },
                        {
                            "name": "customer_purchasing",
                            "value": "15"
                        },
                        {
                            "name": "default_card",
                            "value": ""
                        },
                        {
                            "name": "order_id",
                            "value": "137"
                        },
                        {
                            "name": "number",
                            "value": ""
                        },
                        {
                            "name": "allow_account_balance",
                            "value": "false"
                        },
                        {
                            "name": "allow_credit_balance",
                            "value": "false"
                        },
                        {
                            "name": "sales_tax",
                            "value": "0"
                        },
                        {
                            "name": "additional_tax",
                            "value": "0"
                        },
                        {
                            "name": "paypal_transaction_id",
                            "value": "0PW75387XC778912A"
                        }
                        ]
                    }
                    }
                    }
        self.assertEqual(response.status_code, 200)
   

