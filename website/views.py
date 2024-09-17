from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
def login_view(request):
    return render(request, 'wrt/login.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_term_view(request):
    return render(request, 'wrt/search.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crawl_broken_links_view(request):
    return render(request, 'wrt/brokenLinks.html')
