from django.urls import path
from utils.broken_links import crawl
from . import views

urlpatterns = [
    path('broken-links', views.search_broken_links, name='broken_links'),
    path('string-match', views.search_text_string, name='string_match'),
    path('search-term', views.search_text_string, name='search_term'),
    path('login', views.api_login, name='api_login'),
    path('logout', views.api_logout, name='api_logout'),
]

