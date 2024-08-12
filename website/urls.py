from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                 # Home page
    path('about/', views.about, name='about'),         # About page
    path('login/', views.login_view, name='login'),    # Login page
    path('logout/', views.logout_view, name='logout'), # Logout page
    path('search/', views.search, name='search'),      # Search page
    
]
