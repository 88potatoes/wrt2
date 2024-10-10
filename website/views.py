from datetime import datetime
import json
import os
import threading
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

from api.serializers import ExportResultsSerializer
from api.utils.export import export_to_excel, export_to_pdf
from api.views import find_broken_links, find_text_string
from django.core.paginator import Paginator

from website.models import SearchQuery, SearchResult


@require_http_methods(["GET", "POST"])
@login_required
def search_term_view(request):
    if request.method == "GET":
        return render(request, "wrt/search.html")
    else:
        data, status = find_text_string(request, from_website=True)

        if status == 200:
            # TODO test that the writing works
            queried_webpages, broken_links, requires_access, output = data
            print(data)

            # writing to database
            new_search = SearchQuery.objects.create(
                user=request.user, type=SearchQuery.QueryType.SEARCH
            )

            for search_term, url in queried_webpages:
                SearchResult.objects.create(
                    searchquery=new_search, url=url, search_text=search_term
                )

            return JsonResponse(data, status=200, safe=False)  # TODO make it safe
        elif status == 400:  # return the errors
            return JsonResponse(data, status=400)


@require_http_methods(["GET", "POST"])
@login_required
def crawl_broken_links_view(request):
    if request.method == "GET":
        return render(request, "wrt/brokenLinks.html")
    elif request.method == "POST":
        data, status = find_broken_links(request, from_website=True)
        if status == 200:
            # TODO test that the writing works
            broken_links, requires_access, output = data
            print(data)

            # writing to database
            for seed_url in output:
                for page in output[seed_url]:
                    pass
                    # TODO replace this with the new schema
                    # past_search = PastSearch.objects.create(
                    #     user=request.user,
                    #     seed_url=seed_url,
                    #     url_from=page,
                    #     search_type="search",
                    # )
                    # past_search.save()
            return JsonResponse(data, status=200, safe=False)  # TODO make it safe
        elif status == 400:  # return the errors
            return JsonResponse(data, status=400)


@require_http_methods(["GET"])
@login_required
def history(request):
    all_queries = SearchQuery.objects.filter(user=request.user)[:30:-1]
    paginator = Paginator(all_queries, 10)

    page_number = request.GET.get(
        "page"
    )  # Get the current page number from the query parameters
    queries = paginator.get_page(page_number)  # Get the corresponding page of results

    context = {"queries": queries}
    return render(request, "wrt/history.html", context)


@require_http_methods(["GET"])
def test_view(request):
    return HttpResponse(f"Hello {request.user.username}, you are authenticated.")


def render_login(request):
    return render(request, "registration/login.html")


@require_http_methods(["GET"])
def create_user_view(request):
    return render(request, "wrt/createUser.html")


def login_view(request):  # TODO don't know if it's necessary so look at removing?
    if request.user.is_authenticated:
        return JsonResponse(
            {"message": "Already logged in, redirecting to main site"}, status=200
        )

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log the user in (this creates a session)
            login(request, user)
            return JsonResponse({"message": "Login successful"}, status=200)
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def logout_view(request):
    logout(request)
    return redirect("/")


@require_http_methods(["POST"])
@login_required
def download(request):
    print(request.body)
    serializer = ExportResultsSerializer(data=json.loads(request.body))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get the directory of the current file (views.py)
    current_dir = os.path.dirname(__file__)

    # Define the temp directory path
    # Adjusts the path to go up one level to wrt2 and then to temp
    temp_dir = os.path.join(current_dir, "..", "temp")

    # Ensure the temp directory exists
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if serializer.is_valid():
        search_results = serializer.validated_data["search_results"]
        broken_links = serializer.validated_data["broken_links"]
        access_required_links = serializer.validated_data["access_required_links"]
        export_type = serializer.validated_data["export_type"]
        search_type = serializer.validated_data["search_type"]
        file_url = ""

        # Export PDF file
        if export_type == "pdf":
            pdf_file_path = os.path.join(temp_dir, f"scrape_results_{timestamp}.pdf")
            export_to_pdf(
                search_results, broken_links, access_required_links, pdf_file_path, search_type
            )
            file_url = f"/temp/scrape_results_{timestamp}.pdf"

        # Export Excel file
        elif export_type == "excel":
            excel_file_path = os.path.join(temp_dir, f"scrape_results_{timestamp}.xlsx")
            export_to_excel(
                search_results, broken_links, access_required_links, excel_file_path, search_type
            )
            file_url = f"/temp/scrape_results_{timestamp}.xlsx"

        return JsonResponse(
            {"message": "Export successful", "file_url": file_url}, status=200
        )  # TODO Change hardcoded Status codes
    else:
        print("Serializer errors 3:", serializer.errors)
        return HttpResponse(serializer.errors, status=400)

def download_view(request, filename):
    # Sanitize the filename
    filename = os.path.basename(filename)

    # Verify allowed file types
    allowed_extensions = [".pdf", ".xlsx", ".csv"]  # Add any other allowed extensions
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise Http404("Invalid file type.")

    # Get the directory of the current file (views.py)
    current_dir = os.path.dirname(__file__)

    # Define the temp directory path
    temp_dir = os.path.join(current_dir, "..", "temp")

    # Construct the full file path
    file_path = os.path.join(temp_dir, filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        raise Http404("File not found.")

    # Open the file and return it in the response with error handling
    try:
        response = FileResponse(open(file_path, "rb"), as_attachment=True)
    except IOError:
        raise Http404("Could not open the file.")

    response["Content-Disposition"] = f"attachment; filename={filename}"

    # Delete the file after sending the response
    def delete_file():
        if os.path.exists(file_path):
            os.remove(file_path)

    threading.Timer(10, delete_file).start()  # Delete after 10 seconds

    return response


@require_http_methods(["GET"])
@login_required
def query_results_view(request, query_id):
    # Fetch the specific SearchQuery using the provided ID
    search_query = get_object_or_404(SearchQuery, id=query_id)
    if search_query.user != request.user:
        return HttpResponseForbidden(
            "You do not have permission to view this search query."
        )
    # Get all results related to this search query
    results: SearchResult = (
        search_query.results.all()
    )  # Using the related_name defined in the model
    search_terms = list(set(result.search_text for result in results))
    context = {
        "search_query": search_query,
        "results": results,
        "search_terms": search_terms,
    }
    return render(
        request, "wrt/query_results.html", context
    )  # Render a template for displaying results
