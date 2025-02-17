from django.urls import path

from . import views

app_name = 'registration'
urlpatterns = [
    path('signin/', views.UserSignin.as_view(), name='signin'),
    path('signup/', ((views.UserSignup.as_view())), name='signup'),
    path('signout/', (views.staff_signout), name='signout'),
    path('newpassword/', views.create_password, name='new-password'),
    
    path('customer/signin/', (views.CustomerSignIn.as_view()), name='customer_signin'),
]
