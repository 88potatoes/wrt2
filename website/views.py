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
from redis import Redis

from wrt2.settings import REDIS_CLIENT
from celery.result import AsyncResult


@require_http_methods(["GET", "POST"])
@login_required
def search_term_view(request):
    r = REDIS_CLIENT
    # print(r)

    if request.method == "GET":
        return render(request, "wrt/search.html")
    else:
        session_key = request.session.session_key
        task_id = r.get(f"task:{session_key}")

        if task_id:
            # Convert bytes to string if necessary
            task_id = task_id.decode("utf-8") if isinstance(task_id, bytes) else task_id
            result = AsyncResult(task_id)

            if result.ready():
                # Task is complete
                response = result.get()
                data, status = response

                # Clean up Redis
                r.delete(f"task:{session_key}")

                if status == 200:
                    queried_webpages = data["search_str_webpages"]
                    data["status"] = "finished"

                    # Save to database
                    new_search = SearchQuery.objects.create(
                        user=request.user, type=SearchQuery.QueryType.SEARCH
                    )

                    for search_term, url in queried_webpages:
                        SearchResult.objects.create(
                            searchquery=new_search, url=url, search_text=search_term
                        )

                    return JsonResponse(data, status=200)
                elif status == 400:
                    return JsonResponse(data, status=400)
            else:
                # Task is still processing
                return JsonResponse({"status": "processing"}, status=202)
        else:
            # No existing task; create a new one
            queued_item = find_text_string.delay(request.body, from_website=True)
            task_id = queued_item.id

            # Store task ID in Redis associated with the session key
            r.set(f"task:{session_key}", task_id, ex=3600)  # Expires in 1 hour

            return JsonResponse({"status": "task started"}, status=202)


# @require_http_methods(["GET", "POST"])
# @login_required
# def search_term_view(request):
#     if request.method == "GET":
#         return render(request, "wrt/search.html")
#     else:
#         print("POSTING SEARCH TERM")

#         if r.in(request.session.session_key, "current_requests"):
#             # check if the request is complete
#             # if it is then get the result, otherwise return a random number
#         else:
#             # add an itemp the queue and put the session key intot he current requests
#             queued_item = find_text_string.delay(request.body, from_website=True)
#             r.lpush("current_requests", request.session.session_key)

#         print(f"request.session.session_key: {request.session.session_key}")

#         print("QUEUED ITEM")
#         response = queued_item.get()
#         print("RESPONSE")
#         print(response)
#         data, status = response
#         print("RECEIVED ITEM")

#         if status == 200:
#             # TODO test that the writing works
#             queried_webpages = data["search_str_webpages"]
#             # broken_links = data['broken_links']
#             # requires_access = data['requires_access']
#             # output = data['output']
#             print(data)

#             # writing to database
#             new_search = SearchQuery.objects.create(
#                 user=request.user, type=SearchQuery.QueryType.SEARCH
#             )

#             for search_term, url in queried_webpages:
#                 SearchResult.objects.create(
#                     searchquery=new_search, url=url, search_text=search_term
#                 )

#             return JsonResponse(data, status=200, safe=False)  # TODO make it safe
#         elif status == 400:  # return the errors
#             return JsonResponse(data, status=400)


@require_http_methods(["GET", "POST"])
@login_required
def crawl_broken_links_view(request):
    r = REDIS_CLIENT

    if request.method == "GET":
        return render(request, "wrt/brokenLinks.html")
    elif request.method == "POST":
        queued_item = find_broken_links.delay(
            json.loads(request.body), from_website=True
        )
        result = queued_item.get()
        print(result)
        data, status = result

        if status == 200:
            # TODO test that the writing works
            broken_links = data["broken_links"]
            # broken_links, requires_access, output = data
            # broken_links, requires_access, output = data
            print(data)

            new_query = SearchQuery.objects.create(
                user=request.user, type=SearchQuery.QueryType.CRAWL
            )

            for link in broken_links:
                SearchResult.objects.create(searchquery=new_query, url=link)

            return JsonResponse(data, status=200, safe=False)  # TODO make it safe
        elif status == 400:  # return the errors
            return JsonResponse(data, status=400)


@require_http_methods(["GET"])
@login_required
def history(request):
    all_queries = SearchQuery.objects.filter(user=request.user)[::-1]
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
                search_results,
                broken_links,
                access_required_links,
                pdf_file_path,
                search_type,
            )
            file_url = f"/temp/scrape_results_{timestamp}.pdf"

        # Export Excel file
        elif export_type == "excel":
            excel_file_path = os.path.join(temp_dir, f"scrape_results_{timestamp}.xlsx")
            export_to_excel(
                search_results,
                broken_links,
                access_required_links,
                excel_file_path,
                search_type,
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

    urls_list = [[result.search_text, result.url] for result in results]

    query_type = search_query.type

    context = {
        "search_query": search_query,
        "results": results,
        "urls_list": urls_list,
        "search_terms": search_terms,
        "query_type": query_type,
    }
    return render(
        request, "wrt/query_results.html", context
    )  # Render a template for displaying results
