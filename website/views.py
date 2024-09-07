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
