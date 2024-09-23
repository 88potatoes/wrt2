from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('', views.login_view, name='login'),    # Login page # TODO remove this line because there is another login view
    path('search_term', views.search_term_view,
         name='search_term'),    # Search term
    path('crawl_broken_links', views.crawl_broken_links_view,
         name='crawl_broken_links'),    # Broken links
    # path('', views.history_view, name='login'),    # History
    path('', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset/',
         auth_views.PasswordResetView.as_view(), name='password_reset'),
    path("test", views.test_view, name="test_view"),
    path('create_user', views.create_user_view, name='create_user')
]
