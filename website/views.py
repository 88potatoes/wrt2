from django.shortcuts import render

def login_view(request):
    print("Login view called")
    error = None
    return render(request, 'wrt/login.html', {'error': error})

