from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from . import views

urlpatterns = [
    # Search Pages
    path('search/', views.search_text_string, name='search_api'),
    path('crawl/', views.search_broken_links, name='crawl_api'),
    path('export/', views.export_results, name='export_api'),

    # Login & Token handling
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('temp/', views.temp_view, name='temp_view'),
]

