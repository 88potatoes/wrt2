import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout, views as auth_views
from requests import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import SearchTermSerializer
from api.utils.string_match import scrape
from website.models import PastSearch


@require_http_methods(["GET", "POST"])
@login_required
def search_term_view(request):
    if request.method == "GET":
        return render(request, "wrt/search.html")
    else:  # POST method
        print(f"DATA: {request.body}")
        serializer = SearchTermSerializer(
            data=json.loads(request.body)
        )  # Use request.POST for form data
        if serializer.is_valid():
            search_text = serializer.validated_data["search_text"]
            starting_links = serializer.validated_data["starting_links"]
            browser_info = serializer.validated_data["browser_info"]

            # Call your scraping function here
            result = scrape(starting_links, search_text, browser_info)
            print(f"Result: {result}")

            # Writing history to database as before
            queried_webpages, broken_links, requires_access, output = result

            # writing to database
            for seed_url in output:
                for page in output[seed_url]:
                    past_search = PastSearch.objects.create(
                        user=request.user,
                        seed_url=seed_url,
                        url_from=page,
                        search_type="search",
                        search_text=search_text,
                    )
                    past_search.save()

            return JsonResponse(result, status=200, safe=False)  # TODO make safe True
        else:
            print("Serializer errors 1:", serializer.errors)
            return HttpResponse(serializer.errors, status=400)


@require_http_methods(["GET"])
@login_required
def crawl_broken_links_view(request):
    return render(request, "wrt/brokenLinks.html")


@require_http_methods(["GET"])
@login_required
def history(request):
    return render(request, "wrt/history.html")


@require_http_methods(["GET"])
def test_view(request):
    return HttpResponse(f"Hello {request.user.username}, you are authenticated.")


def render_login(request):
    return render(request, "registration/login.html")


@require_http_methods(["GET"])
def create_user_view(request):
    return render(request, "wrt/createUser.html")


def login_view(request):
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


class CustomLoginView(auth_views.LoginView):
    def form_valid(self, form):
        # Call the original form_valid method to log in the user
        response = super().form_valid(form)

        user = self.request.user
        if not user:  # handling the no user error
            return response

        # generating access token for the user # TODO maybe remove if this is not necessary
        token = AccessToken.for_user(user)
        print(f"Access token: {token}")

        return response
