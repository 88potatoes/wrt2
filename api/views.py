from rest_framework.response import Response
from utils.broken_links import crawl
from utils.string_match import scrape
from django.views.decorators.csrf import csrf_exempt
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

# Search Text String API
@api_view(["POST"])
def search_text_string(request):
    print("Request method:", request.method)
    serializer = SearchTermSerializer(data=request.data)

    if serializer.is_valid():
        search_text = serializer.validated_data['search_text']
        starting_links = serializer.validated_data['starting_links']
        json_filename = serializer.validated_data['json_filename']

        result = scrape(starting_links, json_filename, search_text)
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Broken Links API
@api_view(["POST"])
def search_broken_links(request):
    print("Request data:", request.data)
    serializer = BrokenLinksSerializer(data=request.data)

    if serializer.is_valid():
        starting_links = serializer.validated_data['starting_links']
        json_filename = serializer.validated_data['json_filename']

        result = crawl(starting_links, json_filename)
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)