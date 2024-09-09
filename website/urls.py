from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),                # Home page
    path('', views.login_view, name='login'),    # Login page
]
