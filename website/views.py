
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
@login_required
def search_term_view(request):
    return render(request, 'wrt/search.html')


@require_http_methods(["GET"])
@login_required
def crawl_broken_links_view(request):
    return render(request, 'wrt/brokenLinks.html')


@require_http_methods(["GET"])
def test_view(request):
    return HttpResponse(f"Hello {request.user.username}, you are authenticated.")


@require_http_methods(["GET"])
def create_user_view(request):
    print("Create User view accessed")
    return render(request, 'wrt/createUser.html')
