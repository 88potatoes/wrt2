from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from json import loads
from utils.broken_links import crawl
from utils.string_match import scrape
from api.models import PastSearch
import traceback


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
    
    past_searches = PastSearch.objects.filter(user=request.user, search_type='search').order_by('-created_at')
    past_crawls = PastSearch.objects.filter(user=request.user, search_type='crawl').order_by('-created_at')

    if request.method == "GET":
        return render(request, 'wrt/search.html', {
            'past_searches': past_searches,
            'past_crawls': past_crawls,
        })

    if request.method == 'POST':
        print("Search view called")
        try:
            data = loads(request.body)
            starting_links = data.get('starting_links', [])
            json_filename = data.get('json_filename')
            search_text = data.get('search_text')

            if not starting_links or not json_filename or not search_text:
                return JsonResponse({'error': 'Missing required parameters.'})

            queried_pages = scrape(starting_links, json_filename, search_text)

            PastSearch.objects.create(
                user=request.user,
                search_text=search_text,
                starting_links=', '.join(starting_links),
                json_filename=json_filename,
            )

            if queried_pages:
                return JsonResponse({'message': 'Links crawled successfully!', 'links': queried_pages})
            else:
                return JsonResponse({'message': 'No instances of text found.'})

        except Exception as e:
            return JsonResponse({'message': 'exception', 'error': str(e)})
    else:
        return JsonResponse({'message': 'error', 'error': str(e)})


def crawl_view(request):
    print("Crawl view called")
    if request.method == 'POST':
        try:
            data = loads(request.body)
            starting_links = data.get('starting_links', [])
            json_filename = data.get('json_filename')

            if not starting_links or not json_filename:
                return JsonResponse({'error': 'Missing required parameters.'})

            broken_links = crawl(starting_links, json_filename)

            PastSearch.objects.create(
                user=request.user,  # assuming user is logged in
                starting_links=starting_links,
                json_filename=json_filename,
                search_type='crawl'
            )

            if broken_links:
                return JsonResponse({'message': 'Links crawled successfully!', 'links': broken_links})
            else:
                return JsonResponse({'message': 'No broken links found.'})

        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method.'})
