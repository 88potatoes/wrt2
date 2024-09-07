from django.urls import path
from utils.broken_links import crawl
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from . import views

urlpatterns = [
    path('broken-links', views.search_broken_links, name='broken_links'),
    path('string-match', views.search_text_string, name='string_match'),
    path('search-term', views.search_text_string, name='search_term'),
    path('login', views.api_login, name='api_login'),
    path('logout', views.api_logout, name='api_logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('temp/', views.temp_view, name='temp_view'),
    path('search-page/', views.render_search_view, name='render_search_view'),
    path('search/', views.search_api, name='search_api'),
    path('crawl/', views.crawl_api, name='crawl_api'),
]

