# from django.db import models
# from django.contrib.auth.models import User


# Create your models here.
# class PastSearch(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     search_text = models.CharField(
#         max_length=255, blank=True, null=True
#     )  # For normal searches
#     starting_links = models.TextField()
#     # json_filename = models.CharField(max_length=255) # TODO remove the JSON filename
#     search_type = models.CharField(
#         max_length=50, choices=[("search", "Search"), ("crawl", "Crawl")]
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     seed_url = models.CharField(max_length=255, default="")
#     url_from = models.CharField(max_length=255, default="")
#     url_to = models.CharField(
#         max_length=255, null=True
#     )  # for when the search is broken link

#     def __str__(self):
#         return f"{self.search_text} - {self.created_at}"


# - id
# - user_id
# - seed_url
# - url_from
# - url_to
# - crawl / search
# - created_at
# - search_text (if it’s search)
