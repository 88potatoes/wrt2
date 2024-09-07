from rest_framework.response import Response
from utils.broken_links import crawl
from utils.string_match import scrape
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from pprint import pprint
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import SearchTermSerializer, BrokenLinksSerializer

# Login
@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    next_url = request.data.get('next', '/')

    if not next_url:
        next_url = '/'

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        print("User logged in successfully")
        return Response({"message": "Login successful", "next_url": next_url}, status=status.HTTP_200_OK)
    else:
        print("User flopped log in")
        return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)

# Logouts    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_api(request):
    try:
        data = request.data
        starting_links = data.get('starting_links', [])
        json_filename = data.get('json_filename')
        search_text = data.get('search_text')

        if not starting_links or not json_filename or not search_text:
            return Response({'error': 'Missing required parameters.'}, status=400)

        # Call scrape without saving to the database
        queried_pages = scrape(starting_links, json_filename, search_text)

        if queried_pages:
            return Response({'message': 'Links crawled successfully!', 'links': queried_pages})
        else:
            return Response({'message': 'No instances of text found.'})
    except Exception as e:
        return Response({'message': 'exception', 'error': str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crawl_api(request):
    try:
        data = request.data
        starting_links = data.get('starting_links', [])
        json_filename = data.get('json_filename')

        if not starting_links or not json_filename:
            return Response({'error': 'Missing required parameters.'}, status=400)

        # Call crawl without saving to the database
        broken_links = crawl(starting_links, json_filename)

        if broken_links:
            return Response({'message': 'Links crawled successfully!', 'links': broken_links})
        else:
            return Response({'message': 'No broken links found.'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@permission_classes([IsAuthenticated])
def render_search_view(request):
    return render(request, 'wrt/search.html')

@permission_classes([IsAuthenticated])
def temp_view(request):
    return render(request, 'wrt/temp.html')

# Search Text String API
@api_view(["POST"])
def search_text_string(request):
    serializer = SearchTermSerializer(data=request.data)
    print("Request method:", request.method)

    if serializer.is_valid():
        search_text = serializer.validated_data['search_text']
        starting_links = serializer.validated_data['starting_links']
        json_filename = serializer.validated_data['json_filename']

        result = scrape(starting_links, json_filename, search_text)
        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 1:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Broken Links API
@api_view(["POST"])
def search_broken_links(request):
    print("Request data:", request.data)
    serializer = BrokenLinksSerializer(data=request.data)
    print("Request method:", request.method)

    if serializer.is_valid():
        starting_links = serializer.validated_data['starting_links']
        json_filename = serializer.validated_data['json_filename']

        result = crawl(starting_links, json_filename)
        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 2:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
def temp_view(request):
    return render(request, 'wrt/temp.html')