class BrokenLinksResponse:
    def __init__(self):
        self.broken_links = [] 
        self.requires_access = [] # Pages requiring access (401 or 403 status)
        self.output = {} # Crawled pages organized by the starting URL

class StringMatchResponse(BrokenLinksResponse):
    def __init__(self):
        super().__init__()
        self.search_str_webpages = []  # URLs with matched fragments (for highlighting browsers) /  Pages where search term was found
