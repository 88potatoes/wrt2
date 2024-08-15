from django.urls import path
from utils.broken_links import crawl
from . import views

urlpatterns = [
    path('broken-links', views.search_broken_links, name='broken_links'),
    path('string-match', views.search_text_string, name='string_match'),
]

