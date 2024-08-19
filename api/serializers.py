from rest_framework import serializers

class SearchTermSerializer(serializers.Serializer):
    starting_links = serializers.URLField(required=True)
    json_filename = serializers.CharField(required=True)
    search_text = serializers.CharField(required=True)

class BrokenLinksSerializer(serializers.Serializer):
    starting_links = serializers.URLField(required=True)
    json_filename = serializers.CharField(required=True)