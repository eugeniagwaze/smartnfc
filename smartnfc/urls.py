
from django.contrib import admin
from django.urls import include, path
from smartnfc import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from .views import *

# app_name = 'smartnfc'
urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('signup', views.register, name='signup'),
    path('dashboard_user', views.user_dashboard, name='dashboard_user'),
    path('dashboard_company', views.company_dashboard, name='dashboard_company'),
    path('dashboard_admin', views.admin_dashboard, name='dashboard_admin'),
    path('account', views.profile, name='account'),
    
    path('wallet', views.wallet, name='wallet'),
    path('deposit', views.deposit, name='deposit'),
    path('withdraw', views.withdraw, name='withdraw'),
    path('transcations', views.transcations, name='transcations'),
    path('process_wallet/<int:pk>/',views.wallet_detail, name='process_wallet'),
    path('paynow_payment/', views.paynow_payment, name="paynow_payment"),
    path('paynow_mobile_payment/', views.paynow_mobile_payment, name="paynow_mobile_payment"),
    path('paynows_return/<str:payment_reference>/', views.paynows_return, name="paynows_return"),
    path('paynows_update/<str:payment_reference>/', views.paynows_update, name="paynows_update"),
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/dashboard/<str:username>/', UserDashboardAPIView.as_view(), name='dashboardapi'),
    path('api/withdraw/<str:username>/', WithdrawAPIView.as_view(), name='withdrawalapi'),
    path('api/deposit/<str:username>/', DepositAPIView.as_view(), name='depositapi'),
    path('api/credit/<str:username>/', CreditAPIView.as_view(), name='creditapi'),
     path('api/payment/<str:username>/', PaymentAPIView.as_view(), name='paymentapi'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
