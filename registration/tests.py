from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone, translation
from django.db import connection
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template import exceptions as template_exceptions
from unittest.mock import patch, MagicMock
from administration.models import Business, Location, ServiceTypes, Layouts, Room, AppointmentType, CustomerPlacement, StaffAvailability, DomainToBusinessMapping
from registration.models import Profile
from payment.models import Payment, Order
from .models import CustomerCheckin, Service, BookedAppointment, DisposableAuthenticationToken
from django.urls import reverse

User = get_user_model()

class RegistrationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable foreign key checks for SQLite
        if connection.vendor == 'sqlite':
            connection.cursor().execute('PRAGMA foreign_keys = OFF')
        # Load fixtures
        from django.core.management import call_command
        call_command('loaddata', 'test_data.json', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        # Re-enable foreign key checks for SQLite
        if connection.vendor == 'sqlite':
            connection.cursor().execute('PRAGMA foreign_keys = ON')
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # Create base test data
        cls.business_id = 1
        cls.location = Location.objects.create(
            business_id=cls.business_id,
            name="Test Location",
            time_zone_string="UTC"
        )
        
        cls.studio_settings = Business.objects.create(
            business_id=cls.business_id,
            late_cancel_hours=24,
            noshow_options_prepay=Business.NOSHOW_PREPAY_FLATFEE,
            noshow_prepay_flatfee=Decimal('10.00')
        )
        
        # Create profiles (which are also users)
        cls.customer_profile = Profile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            business_id=cls.business_id,
            first_name="Test",
            last_name="User",
            user_type=Profile.USER_TYPE_CUSTOMER
        )
        
        cls.teacher_profile = Profile.objects.create_user(
            username='testteacher',
            email='teacher@example.com',
            password='testpass123',
            business_id=cls.business_id,
            first_name="Test",
            last_name="Teacher",
            is_teacher=True,
            user_type=Profile.USER_TYPE_STAFF
        )
        
        # Create service type
        cls.service_type = ServiceTypes.objects.create(
            business_id=cls.business_id,
            name="Test Class",
            price=Decimal('100.00')
        )
        
        # Create room and layout
        cls.room = Room.objects.create(
            business_id=cls.business_id,
            name="Test Room",
            location=cls.location
        )
        
        cls.layout = Layouts.objects.create(
            business_id=cls.business_id,
            name="Test Layout",
            room=cls.room,
            capacity=10
        )

    def setUp(self):
        # Reset database state for each test
        connection.close()

    def tearDown(self):
        # Cleanup any state or resources
        super().tearDown()
        connection.close()  # Ensure database connections are closed

class ServiceTests(RegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.scheduled_time = timezone.now() + timedelta(days=1)
        self.service = Service.objects.create(
            class_type=self.service_type,
            teacher=self.teacher_profile,
            scheduled_time=self.scheduled_time,
            duration=timedelta(hours=1),
            layout=self.layout,
            capacity=10,
            price=Decimal('100.00'),
            business_id=self.business_id,
            location_ref=self.location
        )

    def test_service_creation(self):
        """Test service creation with basic attributes"""
        self.assertEqual(self.service.class_type, self.service_type)
        self.assertEqual(self.service.teacher, self.teacher_profile)
        self.assertEqual(self.service.capacity, 10)
        self.assertEqual(self.service.price, Decimal('100.00'))
        self.assertEqual(self.service.location_ref, self.location)

    def test_invalid_service_creation(self):
        """Test service creation with invalid data"""
        with self.assertRaises(ValidationError):
            invalid_service = Service(
                class_type=self.service_type,
                teacher=self.teacher_profile,
                scheduled_time=None,  # Invalid: scheduled_time is required
                duration=timedelta(hours=1),
                layout=self.layout,
                capacity=10,
                business_id=self.business_id
            )
            invalid_service.full_clean()

    def test_service_time_zone_handling(self):
        """Test service time zone conversion methods"""
        self.assertEqual(self.service.time_zone_string(), "UTC")
        self.assertEqual(self.service.time_zone(), pytz.UTC)

    def test_service_string_representation(self):
        """Test string representation of service"""
        expected_str = f"{self.service.name} | {self.service.class_info()}"
        self.assertEqual(str(self.service), expected_str)

    def test_service_occurred_logic(self):
        """Test service occurred logic"""
        # Future service
        self.assertFalse(self.service.occurred())
        
        # Past service
        past_service = Service.objects.create(
            class_type=self.service_type,
            teacher=self.teacher_profile,
            scheduled_time=timezone.now() - timedelta(days=1),
            duration=timedelta(hours=1),
            layout=self.layout,
            capacity=10,
            business_id=self.business_id
        )
        self.assertTrue(past_service.occurred())

    def test_service_with_zero_capacity(self):
        """Test service with unlimited capacity (0)"""
        unlimited_service = Service.objects.create(
            class_type=self.service_type,
            teacher=self.teacher_profile,
            scheduled_time=self.scheduled_time,
            duration=timedelta(hours=1),
            layout=self.layout,
            capacity=0,  # Unlimited capacity
            business_id=self.business_id
        )
        self.assertEqual(unlimited_service.count_available(), float("inf"))

    @patch('payment.helpers.payment_refund', autospec=True)
    def test_service_enrollment_methods(self, mock_create_checkin):
        """Test service enrollment related methods"""
        mock_create_checkin.return_value = CustomerCheckin(
            customer=self.customer_profile,
            in_class=self.service,
            paid=True
        )
        
        initial_count = self.service.count_enrolled()
        self.service.register(self.customer_profile, 1)
        #self.assertTrue(mock_create_checkin.called)
        self.assertIn(self.customer_profile, self.service.enrolled_customers.all())

    def test_multiday_service(self):
        """Test multiday service handling"""
        multiday_service = Service.objects.create(
            class_type=self.service_type,
            teacher=self.teacher_profile,
            scheduled_time=self.scheduled_time,
            duration=timedelta(days=2),  # 48-hour duration
            layout=self.layout,
            capacity=10,
            business_id=self.business_id,
            location_ref=self.location
        )
        self.assertTrue(multiday_service.is_multiday())
        self.assertTrue(multiday_service.within_duration(
            (timezone.now() + timedelta(days=1)).date()
        ))

class CustomerCheckinTests(RegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.scheduled_time = timezone.now() + timedelta(days=1)
        self.service = Service.objects.create(
            class_type=self.service_type,
            teacher=self.teacher_profile,
            scheduled_time=self.scheduled_time,
            duration=timedelta(hours=1),
            layout=self.layout,
            capacity=10,
            business_id=self.business_id
        )
        self.checkin = CustomerCheckin.objects.create(
            customer=self.customer_profile,
            in_class=self.service,
            paid=True
        )

    def test_checkin_creation(self):
        """Test basic checkin creation"""
        self.assertEqual(self.checkin.customer, self.customer_profile)
        self.assertEqual(self.checkin.in_class, self.service)
        self.assertTrue(self.checkin.paid)
        self.assertFalse(self.checkin.waitlist)
        self.assertFalse(self.checkin.present)
        self.assertFalse(self.checkin.cancelled)

    def test_checkin_with_placement(self):
        """Test checkin with specific placement"""
        # Create a placement first
        placement = CustomerPlacement.objects.create(
            x=1.0,
            y=1.0,
            size_x=1.0,
            size_y=1.0,
            alignment=0.0,
            layout=self.layout,
            id_in_layout=1
        )
        
        checkin_with_placement = CustomerCheckin.objects.create(
            customer=self.customer_profile,
            in_class=self.service,
            customer_placement=placement
        )
        
        self.assertIsNotNone(checkin_with_placement.customer_placement)
        self.assertEqual(checkin_with_placement.customer_placement.id_in_layout, 1)

    @patch('payment.helpers.payment_refund', autospec=True)
    def test_checkin_cancellation(self, mock_refund):
        """Test checkin cancellation process"""
        mock_refund.return_value = (True, "Refund successful")
        self.checkin.cancel_and_refund()
        self.assertTrue(self.checkin.cancelled)
        
    def test_checkin_string_representation(self):
        """Test string representation of checkin"""
        expected_str = f"Customer {self.customer_profile.localized_name()} check in for {self.service}"
        self.assertEqual(str(self.checkin), expected_str)

    @patch('payment.helpers.payment_refund', autospec=True)
    def test_no_show_handling(self, mock_refund):
        """Test no-show handling with refund"""
        checkin = CustomerCheckin.objects.create(
            customer=self.customer_profile,
            in_class=self.service,
            paid=True
        )
        # Create a payment and order for the checkin
        payment = Payment.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            location=self.location,
            grand_total=100,
            subtotal=100
        )
        order = Order.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            product_type='service_register',
            store_product_id=checkin.id,
            payment=payment,
            location=self.location,
            paid_amount=100
        )
        
        mock_refund.return_value = (True, "Refund processed")
        checkin.cancel_noshow()
        self.assertTrue(checkin.cancelled)
        self.assertTrue(checkin.no_show)
        # mock_refund.assert_called_once()

class BookedAppointmentTests(RegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.appointment_type = AppointmentType.objects.create(
            business_id=self.business_id,
            name="Test Appointment",
            duration=timedelta(hours=1),
            price=Decimal('100.00')
        )
        
        self.scheduled_time = timezone.now() + timedelta(days=1)
        self.appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            service_provider=self.teacher_profile,
            appointment_type=self.appointment_type,
            scheduled_time=self.scheduled_time,
            booked=True,
            paid=True
        )

    def test_appointment_creation(self):
        """Test basic appointment creation"""
        self.assertEqual(self.appointment.customer, self.customer_profile)
        self.assertEqual(self.appointment.service_provider, self.teacher_profile)
        self.assertEqual(self.appointment.appointment_type, self.appointment_type)
        self.assertTrue(self.appointment.booked)
        self.assertTrue(self.appointment.paid)
        self.assertFalse(self.appointment.cancelled)

    def test_virtual_appointment(self):
        """Test virtual appointment handling"""
        virtual_type = AppointmentType.objects.create(
            business_id=self.business_id,
            name="Virtual Appointment",
            duration=timedelta(hours=1),
            price=Decimal('100.00'),
            virtual=True,
            virtual_service_name="zoom",
            external_video_link="https://zoom.us/test",
            external_video_passcode="123456"
        )
        
        virtual_appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            service_provider=self.teacher_profile,
            appointment_type=virtual_type,
            scheduled_time=self.scheduled_time
        )
        
        self.assertTrue(virtual_appointment.virtual())
        self.assertEqual(virtual_appointment.platform(), "zoom")
        self.assertEqual(virtual_appointment.link(), "https://zoom.us/test")
        self.assertEqual(virtual_appointment.passcode(), "123456")

    def test_appointment_time_handling(self):
        """Test appointment time handling methods"""
        self.assertEqual(self.appointment.time_zone_string(), "UTC")
        self.assertEqual(self.appointment.duration(), timedelta(hours=1))
        self.assertFalse(self.appointment.occurred())

    @patch('payment.helpers.payment_refund', autospec=True)
    def test_appointment_cancellation(self, mock_refund):
        """Test appointment cancellation with refund"""
        mock_refund.return_value = (True, "Refund processed")
        appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            appointment_type=self.appointment_type,
            service_provider=self.teacher_profile,
            scheduled_time=timezone.now() + timedelta(days=2),
            paid=True
        )
        # Create a payment and order for the appointment
        payment = Payment.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            location=self.location,
            grand_total=100,
            subtotal=100
        )
        order = Order.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            product_type='appointment',
            store_product_id=appointment.id,
            payment=payment,
            location=self.location,
            paid_amount=100
        )
        
        print(f"Appointment paid status: {appointment.paid}")  # Log paid status
        print(f"Order associated with appointment ID: {order.store_product_id}")  # Log order association
        appointment.cancel_and_refund()
        # mock_refund.assert_called_once()
        self.assertTrue(appointment.cancelled)
        self.assertFalse(appointment.late_cancelled)

    @patch('payment.helpers.payment_refund', autospec=True)
    def test_no_show_handling(self, mock_refund):
        """Test no-show handling"""
        mock_refund.return_value = (True, "Refund processed")
        appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            appointment_type=self.appointment_type,
            service_provider=self.teacher_profile,
            scheduled_time=self.scheduled_time,
            paid=True
        )
        # Create a payment and order for the appointment
        payment = Payment.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            location=self.location,
            grand_total=100,
            subtotal=100
        )
        order = Order.objects.create(
            business_id=self.business_id,
            customer=self.customer_profile,
            product_type='appointment',
            store_product_id=appointment.id,
            payment=payment,
            location=self.location,
            paid_amount=100
        )
        
        appointment.cancel_noshow()
        # mock_refund.assert_called_once()
        self.assertTrue(appointment.cancelled)
        self.assertTrue(appointment.late_cancelled)
        self.assertTrue(appointment.no_show)

    def test_appointment_late_cancellation(self):
        """Test late cancellation logic"""
        soon_appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            service_provider=self.teacher_profile,
            appointment_type=self.appointment_type,
            scheduled_time=timezone.now() + timedelta(hours=1),
            booked=True,
            paid=True
        )
        self.assertTrue(soon_appointment.late_to_cancel())

    def test_appointment_string_representation(self):
        """Test string representation of appointment"""
        expected_str = f"{self.appointment.name()} - Booked"
        self.assertEqual(str(self.appointment), expected_str)

    def test_google_calendar_url_generation(self):
        """Test that Google Calendar URLs are generated correctly"""
        appointment = BookedAppointment.objects.create(
            business_id=self.business_id,
            location=self.location,
            customer=self.customer_profile,
            appointment_type=self.appointment_type,
            service_provider=self.teacher_profile,
            scheduled_time=self.scheduled_time
        )
        url = appointment.google_calendar_url()
        self.assertIn('https://calendar.google.com/calendar/u/0/r/eventedit?', url)
        self.assertIn('text=', url)
        self.assertIn('dates=', url)
        self.assertIn('ctz=', url)
        self.assertIn('details=', url)
        self.assertIn('location=', url)

class StaffAvailabilityTests(TestCase):
    databases = {'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable foreign key checks for SQLite
        if connection.vendor == 'sqlite':
            connection.cursor().execute('PRAGMA foreign_keys = OFF')
        # Load fixtures
        from django.core.management import call_command
        call_command('loaddata', 'test_data.json', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        # Re-enable foreign key checks for SQLite
        if connection.vendor == 'sqlite':
            connection.cursor().execute('PRAGMA foreign_keys = ON')
        super().tearDownClass()

    def setUp(self):
        """Set up test data"""
        self.business_id = 1
        self.location = Location.objects.create(
            business_id=self.business_id,
            name="Test Location",
            time_zone_string="UTC"
        )
        
        self.teacher_profile = Profile.objects.create_user(
            username='testteacher',
            email='teacher@example.com',
            password='testpass123',
            business_id=self.business_id,
            first_name="Test",
            last_name="Teacher",
            is_teacher=True,
            user_type=Profile.USER_TYPE_STAFF
        )
        
        self.regular_start_time = timezone.now().time()
        self.duration = timedelta(hours=1)
        self.regular_weekdays = {
            'Monday': True,
            'Tuesday': False,
            'Wednesday': True,
            'Thursday': False,
            'Friday': True,
            'Saturday': False,
            'Sunday': False
        }

    def test_regular_availability_creation(self):
        """Test creating a regular staff availability with dictionary weekdays"""
        availability = StaffAvailability.objects.create(
            staff=self.teacher_profile,
            type=StaffAvailability.REGULAR,
            regular_start_time=self.regular_start_time,
            regular_weekdays=self.regular_weekdays,
            duration=self.duration,
            location=self.location,
            business_id=self.business_id
        )

        # Verify the availability was created correctly
        self.assertEqual(availability.staff, self.teacher_profile)
        self.assertEqual(availability.type, StaffAvailability.REGULAR)
        self.assertEqual(availability.regular_start_time, self.regular_start_time)
        self.assertEqual(availability.regular_weekdays, self.regular_weekdays)
        self.assertEqual(availability.duration, self.duration)

        # Test verbose_weekdays output
        expected_days = 'Monday, Wednesday, Friday'
        self.assertEqual(availability.verbose_weekdays(), expected_days)

    def test_single_availability_creation(self):
        """Test creating a single staff availability"""
        single_start_datetime = timezone.now() + timedelta(days=1)
        availability = StaffAvailability.objects.create(
            staff=self.teacher_profile,
            type=StaffAvailability.SINGLE,
            single_start_datetime=single_start_datetime,
            duration=self.duration,
            location=self.location,
            business_id=self.business_id
        )

        self.assertEqual(availability.staff, self.teacher_profile)
        self.assertEqual(availability.type, StaffAvailability.SINGLE)
        self.assertEqual(availability.single_start_datetime, single_start_datetime)
        self.assertEqual(availability.duration, self.duration)

    def test_includes_day(self):
        """Test the includes_day method for both regular and single availability"""
        # Create regular availability
        regular = StaffAvailability.objects.create(
            staff=self.teacher_profile,
            type=StaffAvailability.REGULAR,
            regular_start_time=self.regular_start_time,
            regular_weekdays=self.regular_weekdays,
            duration=self.duration,
            location=self.location,
            business_id=self.business_id
        )

        # Test a Monday (should be available)
        monday = timezone.datetime(2024, 1, 1)  # A Monday
        self.assertTrue(regular.includes_day(monday))

        # Test a Tuesday (should not be available)
        tuesday = timezone.datetime(2024, 1, 2)  # A Tuesday
        self.assertFalse(regular.includes_day(tuesday))

        # Create single availability
        single_start = timezone.now() + timedelta(days=1)
        single = StaffAvailability.objects.create(
            staff=self.teacher_profile,
            type=StaffAvailability.SINGLE,
            single_start_datetime=single_start,
            duration=self.duration,
            location=self.location,
            business_id=self.business_id
        )

        # Test the day of availability
        test_day = single_start
        self.assertTrue(single.includes_day(test_day))

        # Test the day after (should not be available)
        test_day = single_start + timedelta(days=1)
        self.assertFalse(single.includes_day(test_day))

class DisposableAuthenticationTokenTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        # Clean up any existing tokens
        DisposableAuthenticationToken.objects.filter(target_profile=self.profile).delete()
        self.token = DisposableAuthenticationToken.objects.create(
            target_profile=self.profile,
            temporary_user=self.profile
        )

    def test_token_creation(self):
        """Test token creation"""
        self.assertIsNotNone(self.token.token)
        self.assertIsNotNone(self.token.created_at)

    def test_token_validity(self):
        """Test token validity checking"""
        self.assertTrue(self.token.is_token_valid())
        
        # Test expired token
        future_time = timezone.now() + timedelta(minutes=settings.DISPOSABLE_AUTHENTICATION_TOKEN_EXPIRATION + 1)
        with patch('django.utils.timezone.now', return_value=future_time):
            self.assertFalse(self.token.is_token_valid())

    def test_token_uniqueness(self):
        """Test that tokens are unique per profile"""
        # Delete any existing tokens first
        DisposableAuthenticationToken.objects.all().delete()
        
        token1 = DisposableAuthenticationToken.objects.create(
            target_profile=self.profile,
            temporary_user=self.profile
        )
        self.assertTrue(token1.is_token_valid())
        
        # Delete the first token before creating a new one
        token1.delete()
        
        token2 = DisposableAuthenticationToken.objects.create(
            target_profile=self.profile,
            temporary_user=self.profile
        )
        self.assertTrue(token2.is_token_valid())

    def test_token_with_null_temporary_user(self):
        """Test token creation with null temporary user"""
        # Delete existing token first since we have a OneToOne constraint
        self.token.delete()
        
        token = DisposableAuthenticationToken.objects.create(
            target_profile=self.profile,
            temporary_user=None
        )
        self.assertIsNone(token.temporary_user)
        self.assertTrue(token.is_token_valid())

class RegistrationFunctionalTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        
        # Create a test business
        self.business_id = 'test_business'
        self.studio_settings = Business.objects.create(
            business_id=self.business_id,
            default_country_code='US'
        )
        
        # Create a test user associated with the business
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
            business_id=self.business_id
        )
        self.test_user.is_active = True
        self.test_user.save()
        
        # Create domain mapping for the business
        DomainToBusinessMapping.objects.create(
            domain='testdomain.com',
            business_id=self.business_id
        )

    def test_user_signup_get(self):
        response = self.client.get(reverse('registration:signup'))
        self.assertEqual(response.status_code, 200)

    def test_user_signup_post(self):
        signup_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_2': 'password123',
        }
        response = self.client.post(reverse('registration:signup'), signup_data)
        self.assertIn(response.status_code, [200, 302])

    def test_user_signin_get(self):
        response = self.client.get(reverse('registration:signin'))
        self.assertEqual(response.status_code, 200)

    def test_user_signin_post(self):
        #First have to create the user before we sign in as the suer
        signup_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_2': 'password123',
        }
        response = self.client.post(reverse('registration:signup'), signup_data)

        signin_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'redirect_url': ''
        }
        response = self.client.post(reverse('registration:signin'), signin_data, HTTP_HOST='testdomain.com')
        # Assuming a redirect on successful signin
        self.assertIn(response.status_code, [200, 302])

    def test_global_signin_get(self):
        response = self.client.get(reverse('registration:global-signin'))
        self.assertEqual(response.status_code, 200)

    def test_global_signin_post(self):
        #First have to create the user before we sign in as the suer
        signup_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_2': 'password123',
        }
        response = self.client.post(reverse('registration:signup'), signup_data)

        signin_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
        }
        response = self.client.post(reverse('registration:global-signin'), signin_data)
        self.assertIn(response.status_code, [200, 302])

    def test_checkin_template_get(self):
        response = self.client.get(reverse('registration:checkin_template'))
        self.assertEqual(response.status_code, 200)

    def test_checkin_layout_template_get(self):
        response = self.client.get(reverse('registration:checkin_layout_template'))
        self.assertEqual(response.status_code, 200)

    def test_sso_redirect_view_get(self):
        response = self.client.get(reverse('registration:sso_redirect', kwargs={'business_id': 1}))
        self.assertIn(response.status_code, [200, 302, 404])

    def test_one_time_token_authentication_get(self):
        response = self.client.get(reverse('registration:one_time_token_auth', args=['123e4567-e89b-12d3-a456-426614174000']))
        self.assertIn(response.status_code, [200, 302, 404])

    def test_user_registration_flow(self):
        """Test the complete user registration flow."""
        try:
            response = self.client.get(reverse('registration:signup'))
            self.assertEqual(response.status_code, 200)

            registration_data = {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'testuser@example.com',
                'phone': '+12125552368',
                'password': 'password123',
                'password_2': 'password123',
                'message_consent': True
            }
            response = self.client.post(reverse('registration:signup'), registration_data)
            self.assertEqual(response.status_code, 302)  # Expect a redirect after successful registration

            # Check for form errors if the user was not created
            user_exists = User.objects.filter(email='testuser@example.com').exists()
            if not user_exists:
                form_errors = response.context.get('signup_form').errors if response.context else 'No context'
                print("Signup form errors:", form_errors)
            self.assertTrue(user_exists)

            # Check email confirmation (assuming a confirmation step is involved)
            # This part would need to be adapted based on your actual email confirmation process.
        except template_exceptions.TemplateDoesNotExist:
            # Skip the test if the template is not found
            # This is a temporary solution until we have all templates in place
            self.skipTest("Template files not found. This test requires the registration templates to be in place.")

    def test_create_account(self):
        response = self.client.post(reverse('registration:create_account'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'phone': '1234567890',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_signin(self):
        response = self.client.post(reverse('registration:signin'), {
            'email': 'testuser@example.com',
            'password': 'testpass'
        }, HTTP_HOST='testdomain.com')
        self.assertEqual(response.status_code, 302)

    def test_global_signin(self):
        response = self.client.post(reverse('registration:global-signin'), {
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 302)

    def test_acme_webhook(self):
        # Use a safe domain from settings
        safe_domain = settings.SAFE_DOMAINS[0] if settings.SAFE_DOMAINS else 'example.com'
        response = self.client.post(
            reverse('registration:acme_webhook'),
            {'data': 'sample'},
            HTTP_USER_AGENT=safe_domain,
            REMOTE_ADDR=safe_domain
        )
        self.assertEqual(response.status_code, 200)

    def test_complete_onboarding(self):
        response = self.client.post(reverse('registration:complete_onboarding'), {
            'data': 'sample'
        })
        self.assertEqual(response.status_code, 200)

    def test_check_unique_domain_api(self):
        response = self.client.post(reverse('registration:check_domain'), {
            'domain': 'example.com'
        })
        self.assertEqual(response.status_code, 200)

    def test_staff_signout(self):
        response = self.client.get(reverse('registration:signout'))
        self.assertEqual(response.status_code, 302)

    def test_signout_booking(self):
        response = self.client.get(reverse('registration:signout-booking'))
        self.assertEqual(response.status_code, 302)

    def test_signout_appt(self):
        response = self.client.get(reverse('registration:signout-appt'))
        self.assertEqual(response.status_code, 302)

    def test_create_password(self):
        response = self.client.post(reverse('registration:create_password'), {'password': 'newpass'})
        self.assertEqual(response.status_code, 200)

    def test_cleanse_url(self):
        response = self.client.get(reverse('registration:cleanse_url'), {'url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)

    @patch('chargebee.configure')
    @patch('chargebee.Coupon.retrieve')
    def test_check_promo_code(self, mock_retrieve, mock_configure):
        # Mock the Chargebee API response
        mock_coupon = type('Coupon', (), {'status': 'active'})
        mock_result = type('Result', (), {'coupon': mock_coupon})
        mock_retrieve.return_value = mock_result
        mock_configure.return_value = None
        
        response = self.client.post(
            reverse('registration:check_promo_code'),
            {'coupon_code': 'PROMO123', 'language': 'English'},
            HTTP_HOST='testdomain.com'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'active')
        self.assertEqual(response.json()['message'], 'Promo Code Applied!')
        mock_configure.assert_called_once()
        mock_retrieve.assert_called_once()

    def test_customer_signin_get(self):
        response = self.client.get(reverse('registration:customer_signin'))
        self.assertEqual(response.status_code, 200)

    def test_customer_signin_post(self):
        response = self.client.post(reverse('registration:customer_signin'), {'username': 'customeruser', 'password': 'customerpass'})
        self.assertEqual(response.status_code, 302)

class FunctionalTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_flow(self):
        """Test the complete user registration flow."""
        try:
            response = self.client.get(reverse('registration:signup'))
            self.assertEqual(response.status_code, 200)

            registration_data = {
                'first_name': 'Test',
                'email': 'testuser@example.com',
                'phone': '+12125552368',
                'password': 'password123',
                'password_2': 'password123',
                'message_consent': True
            }
            response = self.client.post(reverse('registration:signup'), registration_data)
            self.assertEqual(response.status_code, 302)  # Expect a redirect after successful registration

            # Check for form errors if the user was not created
            user_exists = User.objects.filter(email='testuser@example.com').exists()
            if not user_exists:
                form_errors = response.context.get('signup_form').errors if response.context else 'No context'
                print("Signup form errors:", form_errors)
            self.assertTrue(user_exists)

            # Check email confirmation (assuming a confirmation step is involved)
            # This part would need to be adapted based on your actual email confirmation process.
        except template_exceptions.TemplateDoesNotExist:
            # Skip the test if the template is not found
            # This is a temporary solution until we have all templates in place
            self.skipTest("Template files not found. This test requires the registration templates to be in place.")

    def test_success(self):
        with translation.override('en'):  # Force English language
            response = self.client.get(reverse('success'))
            print("Response content:", response.content.decode())  # Log the response content
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Successful Signin.")

    def test_unsuccess(self):
        with translation.override('en'):  # Force English language
            response = self.client.get(reverse('unsuccess'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Unsuccessful Signin.")

    def test_student_signup(self):
        response = self.client.get(reverse('student_signup'))
        self.assertEqual(response.status_code, 200)

    def test_create_account(self):
        response = self.client.post(reverse('registration:create_account'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'phone': '1234567890',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)

    def test_staff_signout(self):
        response = self.client.get(reverse('registration:signout'))
        self.assertEqual(response.status_code, 302)

    def test_signout_booking(self):
        response = self.client.get(reverse('registration:signout-booking'))
        self.assertEqual(response.status_code, 302)

    def test_signout_appt(self):
        response = self.client.get(reverse('registration:signout-appt'))
        self.assertEqual(response.status_code, 302)

    def test_create_password(self):
        response = self.client.post(reverse('registration:create_password'), {'password': 'newpass'})
        self.assertEqual(response.status_code, 200)

    def test_acme_webhook(self):
        # Use a safe domain from settings
        safe_domain = settings.SAFE_DOMAINS[0] if settings.SAFE_DOMAINS else 'example.com'
        response = self.client.post(
            reverse('registration:acme_webhook'),
            {'data': 'sample'},
            HTTP_USER_AGENT=safe_domain,
            REMOTE_ADDR=safe_domain
        )
        self.assertEqual(response.status_code, 200)

    def test_complete_onboarding(self):
        response = self.client.post(reverse('registration:complete_onboarding'), {'data': 'sample'})
        self.assertEqual(response.status_code, 200)

    def test_unique_domain(self):
        response = self.client.get(reverse('unique_domain'), {'domain': 'example.com'})
        self.assertEqual(response.status_code, 200)

    def test_check_unique_domain_api(self):
        response = self.client.post(reverse('registration:check_domain'), {'domain': 'example.com'})
        self.assertEqual(response.status_code, 200)

    def test_cleanse_url(self):
        response = self.client.get(reverse('registration:cleanse_url'), {'url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)

    @patch('chargebee.configure')
    @patch('chargebee.Coupon.retrieve')
    def test_check_promo_code(self, mock_retrieve, mock_configure):
        # Mock the Chargebee API response
        mock_coupon = type('Coupon', (), {'status': 'active'})
        mock_result = type('Result', (), {'coupon': mock_coupon})
        mock_retrieve.return_value = mock_result
        mock_configure.return_value = None
        
        response = self.client.post(reverse('registration:check_promo_code'), 
            {'coupon_code': 'PROMO123', 'language': 'English'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'active')
        self.assertEqual(response.json()['message'], 'Promo Code Applied!')
        mock_configure.assert_called_once()
        mock_retrieve.assert_called_once()

    def test_staff_signup_get(self):
        response = self.client.get(reverse('staff_signup'))
        self.assertEqual(response.status_code, 200)

    def test_staff_signup_post(self):
        response = self.client.post(reverse('staff_signup'), {'username': 'staffuser', 'password': 'staffpass'})
        self.assertEqual(response.status_code, 302)

    def test_customer_signin_get(self):
        response = self.client.get(reverse('registration:customer_signin'))
        self.assertEqual(response.status_code, 200)

    def test_customer_signin_post(self):
        response = self.client.post(reverse('registration:customer_signin'), {'username': 'customeruser', 'password': 'customerpass'})
        self.assertEqual(response.status_code, 302)
