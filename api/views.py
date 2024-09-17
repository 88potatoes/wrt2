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

""" 
================================= Login Functions ====
"""
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

""" 
================================= Search Functions =================================
"""
@permission_classes([IsAuthenticated])
def render_search_view(request):
    return render(request, 'wrt/search.html')

# Search Text String API
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def search_text_string(request):
    serializer = SearchTermSerializer(data=request.data)
    print("Request method:", request.method)

    if serializer.is_valid():
        search_text = serializer.validated_data['search_text']
        starting_links = serializer.validated_data['starting_links']
        # json_filename = serializer.validated_data['json_filename']

        result = scrape(starting_links, "a.json", search_text) # TODO we need to decide on the json filename, is that a requirement
        print(result)


        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 1:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Broken Links API
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def search_broken_links(request):
    print("Request data:", request.data)
    serializer = BrokenLinksSerializer(data=request.data)
    print("Request method:", request.method)

    if serializer.is_valid():
        starting_links = serializer.validated_data['starting_links']
        # json_filename = serializer.validated_data['json_filename']

        result = crawl(starting_links)
        print(result) # TODO Remove
        
        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 2:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
def temp_view(request):
    return render(request, 'wrt/temp.html')
