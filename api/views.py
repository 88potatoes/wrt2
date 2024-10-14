import json
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse, FileResponse, Http404
from datetime import datetime
from .serializers import (
    SearchTermSerializer,
    BrokenLinksSerializer,
    ExportResultsSerializer,
)

# from .models import PastSearch
from .utils.broken_links import crawl
from .utils.string_match import scrape
from .utils.export import export_to_excel, export_to_pdf
import os
import threading
from celery import Celery

app = Celery("my_app", broker="redis://localhost:6379/0")

"""
================================= Search APIS =================================
"""


# Search Text String API
@app.task
def find_text_string(request, from_website=False):  # used by the website app
    data = request.body if from_website else request.data
    serializer = SearchTermSerializer(data=json.loads(data))
    print("Request data:", data)
    print("Request method:", request.method)

    if serializer.is_valid():
        search_text = serializer.validated_data["search_text"]
        starting_links = serializer.validated_data["starting_links"]
        browser_info = serializer.validated_data["browser_info"]
        result = scrape(starting_links, search_text, browser_info)

        return (
            Response(result, status=status.HTTP_200_OK)
            if not from_website
            else (result, 200)
        )
    else:
        print("Serializer errors 1:", serializer.errors)
        return (
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if not from_website
            else (serializer.errors, 400)
        )


# Broken Links API
@app.task
def find_broken_links(request, from_website=False):  # used by the website app
    data = request.body if from_website else request.data
    serializer = BrokenLinksSerializer(data=json.loads(data))
    print("Request data:", data)
    print("Request method:", request.method)

    if serializer.is_valid():
        starting_links = serializer.validated_data["starting_links"]

        result = crawl(starting_links)
        print(result)

        return (
            Response(result, status=status.HTTP_200_OK)
            if not from_website
            else (result, 200)
        )
    else:
        print("Serializer errors 2:", serializer.errors)
        return (
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if not from_website
            else (serializer.errors, 400)
        )


@permission_classes([IsAuthenticated])
def temp_view(request):
    return render(request, "wrt/temp.html")
