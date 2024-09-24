from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.sessions.models import Session
from django.shortcuts import render
from django.utils import timezone 
from django.http import JsonResponse, FileResponse, Http404  
from datetime import datetime
from .serializers import SearchTermSerializer, BrokenLinksSerializer, ExportResultsSerializer
from .models import PastSearch
from utils.broken_links import crawl
from utils.string_match import scrape
from utils.export import export_to_excel, export_to_pdf
import os
import threading

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
================================= Search APIS =================================
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

        result = scrape(starting_links, search_text, browser_info)

        # writing history to database
        queried_webpages, broken_links, requires_access, output = result

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

        result = crawl(starting_links)
        print(result) # TODO Remove
        
        return Response(result, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 2:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

""" 
================================= Export and Download APIS =================================
"""

# Export Results API
@api_view(["POST"])
@session_required
@permission_classes([IsAuthenticated])
def export_results(request):
    serializer = ExportResultsSerializer(data=request.data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get the directory of the current file (views.py)
    current_dir = os.path.dirname(__file__)

    # Define the temp directory path
    # Adjusts the path to go up one level to wrt2 and then to temp
    temp_dir = os.path.join(current_dir, '..', 'temp') 

    # Ensure the temp directory exists
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if serializer.is_valid():
        search_results = serializer.validated_data['search_results']
        broken_links = serializer.validated_data['broken_links']
        access_required_links = serializer.validated_data['access_required_links']
        export_type = serializer.validated_data['export_type']
        file_url = ''

        # Export PDF file
        if export_type == 'pdf':
            pdf_file_path = os.path.join(temp_dir, f'scrape_results_{timestamp}.pdf') 
            export_to_pdf(search_results, broken_links, access_required_links, pdf_file_path)
            file_url = f'/temp/scrape_results_{timestamp}.pdf'

        # Export Excel file
        elif export_type == 'excel':
            excel_file_path = os.path.join(temp_dir, f'scrape_results_{timestamp}.xlsx')
            export_to_excel(search_results, broken_links, access_required_links, excel_file_path)
            file_url = f'/temp/scrape_results_{timestamp}.xlsx'

        return Response({'message': 'Export successful', 'file_url': file_url}, status=status.HTTP_200_OK)
    else:
        print("Serializer errors 3:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["GET"])
@session_required
@permission_classes([IsAuthenticated])
def download_view(request, filename):
    # Sanitize the filename
    filename = os.path.basename(filename)

    # Verify allowed file types
    allowed_extensions = ['.pdf', '.xlsx', '.csv']  # Add any other allowed extensions
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise Http404("Invalid file type.")

    # Get the directory of the current file (views.py)
    current_dir = os.path.dirname(__file__)

    # Define the temp directory path
    temp_dir = os.path.join(current_dir, '..', 'temp')

    # Construct the full file path
    file_path = os.path.join(temp_dir, filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        raise Http404("File not found.")

    # Open the file and return it in the response with error handling
    try:
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    except IOError:
        raise Http404("Could not open the file.")
    
    response['Content-Disposition'] = f'attachment; filename={filename}'

    # Delete the file after sending the response
    def delete_file():
        if os.path.exists(file_path):
            os.remove(file_path)

    threading.Timer(60, delete_file).start()  # Delete after 60 seconds

    return response

@permission_classes([IsAuthenticated])
def temp_view(request):
    return render(request, 'wrt/temp.html')
