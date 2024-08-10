from django.http import HttpResponse

def home(request):
    print("Home view called")
    return HttpResponse("<h1>Welcome to the Home Page!</h1>")

def about(request):
    print("About view called")
    return HttpResponse("<h1>About Us</h1>")

