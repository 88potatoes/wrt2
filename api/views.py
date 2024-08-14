from django.http import JsonResponse
from rest_framework.response import Response
from utils.broken_links import crawl
from utils.string_match import scrape


def search_broken_links(request):
    starting_links = request.data.get('starting_links', [])
    json_filename = request.data.get('json_filename', 'output.json')
    return Response(crawl(starting_links, json_filename))

def search_text_string(request):
    starting_links = request.data.get('starting_links', [])
    json_filename = request.data.get('json_filename', 'output.json')
    search_text = request.data.get('search_text', "")

    if not search_text:
        return Response("Specific text required", status=400)

    return Response(scrape(starting_links, json_filename, search_text))



    
