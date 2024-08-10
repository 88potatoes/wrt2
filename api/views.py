from django.http import JsonResponse

def scrape(request):
    data = {"name": "amanda chao"}
    return JsonResponse(data)