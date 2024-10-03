from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class PastSearch(models.Model): # TODO delete this model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_text = models.CharField(
        max_length=255, blank=True, null=True
    )  # For normal searches
    starting_links = models.TextField()
    # json_filename = models.CharField(max_length=255) # TODO remove the JSON filename
    search_type = models.CharField(
        max_length=50, choices=[("search", "Search"), ("crawl", "Crawl")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    seed_url = models.CharField(max_length=255, default="")
    url_from = models.CharField(max_length=255, default="")
    url_to = models.CharField(
        max_length=255, null=True
    )  # for when the search is broken link

    def __str__(self):
        return f"{self.search_text} - {self.created_at}"


class SearchQuery(models.Model):
    class QueryType(models.TextChoices):
        SEARCH = "Search", "Search"
        CRAWL = "Crawl", "Crawl"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_queries"
    )
    type = models.CharField(
        max_length=6, choices=QueryType.choices, default=QueryType.SEARCH
    )
    created_at = models.DateTimeField(auto_now_add=True)


class SearchResult(models.Model):
    searchquery = models.ForeignKey(
        SearchQuery, on_delete=models.CASCADE, related_name="results"
    )
    url = models.CharField(max_length=255, default="")
    url_to = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    starting_link = models.CharField(max_length=255, null=True, blank=True)


# - id
# - user_id
# - seed_url
# - url_from
# - url_to
# - crawl / search
# - created_at
# - search_text (if it’s search)
