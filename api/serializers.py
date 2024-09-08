from rest_framework import serializers

def validate_json_filename(value):
    if not value.endswith('.json'):
        return f"{value}.json"
    return value

def validate_search_text(value):
    value = value.strip()
    if not value:
        raise serializers.ValidationError("Search text cannot be empty or just whitespace.")
    return value

def validate_starting_links(value):
    if not isinstance(value, list):
        raise serializers.ValidationError("Starting links must be a list.")
    
    if not value:
        raise serializers.ValidationError("Starting links list cannot be empty.")
    
    for link in value:
        link = link.strip()
        if not (link.startswith('http://') or link.startswith('https://')):
            raise serializers.ValidationError(f"Invalid URL: {link}. Starting link must start with http:// or https://.")
    return value

class BaseSerializer(serializers.Serializer):
    starting_links = serializers.ListField(
        child=serializers.URLField(),
        required=True
    )
    json_filename = serializers.CharField(required=True, max_length=100)

    def validate_json_filename(self, value):
        return validate_json_filename(value)

    def validate_starting_links(self, value):
        return validate_starting_links(value)

class SearchTermSerializer(BaseSerializer):
    search_text = serializers.CharField(required=True)

    def validate_search_text(self, value):
        return validate_search_text(value)

class BrokenLinksSerializer(BaseSerializer):
    pass
