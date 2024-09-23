
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken

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

def render_login(request):
    return render(request, 'registration/login.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log the user in (this creates a session)
            login(request, user)

            # Generate JWT tokens (access and refresh)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Return both tokens in the response
            return JsonResponse({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'message': 'Login successful',
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('/')