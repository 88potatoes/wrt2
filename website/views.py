from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from json import loads
from broken_links import crawl

def home(request):
    print("Home view called")
    return render(request, 'wrt/index.html')

def about(request):
    print("About view called")
    return render(request, 'wrt/about.html')

def login_view(request):
    print("Login view called")
    error = None

    return render(request, 'wrt/login.html', {'error': error})

def search(request):
    print("Search view called")
    
    if not request.user.is_authenticated:
        print("User not logged in")
        return redirect('/login')
    
    if not request.user.is_superuser:
        print("User is not a superuser")
        return redirect('/')
    
    return render(request, 'wrt/search.html')

def crawl_view(request):
    print("Crawl view called")
    if request.method == 'POST':
        try:
            data = loads(request.body)
            starting_links = data.get('starting_links')
            json_filename = data.get('json_filename')

            if not starting_links or not json_filename:
                return JsonResponse({'error': 'Missing required parameters.'})

            broken_links = crawl(starting_links, json_filename)
            return JsonResponse({'message': 'Crawling completed successfully.', 'broken_links': broken_links})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method.'})