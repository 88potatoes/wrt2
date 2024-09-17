from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),    # Login page
    path('search_term', views.search_term_view, name='search_term'),    # Search term
    path('crawl_broken_links', views.crawl_broken_links_view, name='crawl_broken_links'),    # Broken links
    # path('', views.history_view, name='login'),    # History
]
