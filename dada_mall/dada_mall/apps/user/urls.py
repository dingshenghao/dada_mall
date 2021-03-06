"""dada_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view()),
    path('username/<username>/', views.CheckUsername.as_view()),
    path('email/<email>/', views.CheckEmail.as_view()),
    path('mobile/<phone>/', views.CheckPhone.as_view()),
    path('emails/verify/', views.EmailVerify.as_view()),

    path('login/', views.UserLoginView.as_view()),

    path('users/<username>/address/', views.UserAddressView.as_view()),
    path('users/<username>/address/<int:id>/', views.DeleteAddressView.as_view()),
    path('users/<username>/address/default/', views.DefaultAddressView.as_view()),
    path('users/<username>/password/', views.ChangePasswordView.as_view()),
    path('users/password/sms/', views.FindPaswordView.as_view()),
    path('users/password/verification/', views.VerifyPasswordView.as_view()),
    path('users/password/new/', views.NewPasswordView.as_view()),

]
