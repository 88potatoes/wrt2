from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Main functionalities
    path("search_term", views.search_term_view, name="search_term"),                       # Search term
    path("history", views.history, name="history"),                                        # History
    path("crawl_broken_links", views.crawl_broken_links_view, name="crawl_broken_links"),  # Broken links

    # Authentication
    path("", auth_views.LoginView.as_view(), name="login_page"),
    path("logout", views.logout_view, name="logout"),
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path("create_user", views.create_user_view, name="create_user"),

    # Export
    path("download", views.download, name="download"),
    path("download/<str:filename>/", views.download_view, name="download_from_website"),

    # History
    path(
        "query/<int:query_id>/results/", views.query_results_view, name="query_results"
    ),  # for history
  
    # Test
    path("test", views.test_view, name="test_view"),
]
