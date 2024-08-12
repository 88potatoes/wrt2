from django.db import models 

# Create your models here. 
class SearchHistory(models.Model): 
    id = models.AutoField(primary_key=True) 
    type = models.CharField(max_length=50) 
    search_term = models.CharField(max_length=255) 
    datetime = models.DateTimeField(auto_now_add=True) 

    def __str__(self): 
        return f"{self.type}: {self.search_term} on {self.search_url} at {self.datetime}" 
    
class SearchTerm(models.Model): 
    id = models.AutoField(primary_key=True) 
    term = models.CharField(max_length=255) 

    def __str__(self): 
        return self.term 

class SearchTermWebsite(models.Model): 
    search_term = models.ForeignKey(SearchTerm, related_name='websites', on_delete=models.CASCADE) 
    website_url = models.URLField() 
    position = models.IntegerField() 

    def __str__(self): 
        return f"{self.website_url} at position {self.position} for term {self.search_term.term}"