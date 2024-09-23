from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone 
from django.http import JsonResponse  
import json
import os
from datetime import datetime
from .serializers import SearchTermSerializer, BrokenLinksSerializer
from .models import PastSearch
from utils.broken_links import crawl
from utils.string_match import scrape
from utils.export import export_to_excel, export_to_pdf


""" 
================================= Session Check Functions =================================
"""
def session_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_session_valid(request):
            return JsonResponse({'detail': 'Session expired. Please log in again.'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def is_session_valid(request):
    session_key = request.COOKIES.get('sessionid')
    if not session_key:
        return False
    try:
        session = Session.objects.get(session_key=session_key)
        return session.expire_date and session.expire_date >= timezone.now()
    except Session.DoesNotExist:
        return False

""" 
================================= Search Functions =================================
"""

# Search Text String API
@api_view(["POST"])
@session_required
@permission_classes([IsAuthenticated])
def search_text_string(request):
    serializer = SearchTermSerializer(data=request.data)
    print("Request method:", request.method)

    if serializer.is_valid():
        search_text = serializer.validated_data['search_text']
        starting_links = serializer.validated_data['starting_links']
        browser_info = serializer.validated_data['browser_info']
        # json_filename = serializer.validated_data['json_filename']

        result = scrape(starting_links, search_text, browser_info)
        print("Results: ", result)

        # writing history to database
        queried_webpages, requires_access, output = result

        for seed_url in output:
            for page in output[seed_url]:
                # print(f"{seed_url}: {page}")
                past_search = PastSearch.objects.create(
                    user=request.user,
                    seed_url=seed_url,
                    url_from=page,
                    search_type='search',
                    search_text=search_text,
                )
                past_search.save()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save the result as an Excel file in the local repo
        # Define the path
        file_dir = '/wrt2'
        # excel_file_path = os.path.join(file_dir, f'scrape_results_{timestamp}.xlsx')
        pdf_file_path = os.path.join(file_dir, f'scrape_results_{timestamp}.pdf') 

        # Ensure the directory exists
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        # export_to_excel(queried_webpages, requires_access, result[2], excel_file_path)
        export_to_pdf(queried_webpages, requires_access, result[2], pdf_file_path)

        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 1:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Broken Links API
@api_view(["POST"])
@session_required
@permission_classes([IsAuthenticated])
def search_broken_links(request): # TODO write the results to the database
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
