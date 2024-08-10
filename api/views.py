from django.http import HttpResponse

def scrape(request):
    return HttpResponse("{\"name\": \"amanda chao\"}")