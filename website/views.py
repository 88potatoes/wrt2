from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

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