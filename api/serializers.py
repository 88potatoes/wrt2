from rest_framework import serializers


def validate_json_filename(value):
    if not value.endswith(".json"):
        return f"{value}.json"
    return value


def validate_search_text(value):
    value = value.strip()
    if not value:
        raise serializers.ValidationError(
            "Search text cannot be empty or just whitespace."
        )
    return value


def validate_starting_links(value):
    if not isinstance(value, list):
        raise serializers.ValidationError("Starting links must be a list.")

    if not value:
        raise serializers.ValidationError("Starting links list cannot be empty.")

    for link in value:
        link = link.strip()
        if not (link.startswith("http://") or link.startswith("https://")):
            raise serializers.ValidationError(
                f"Invalid URL: {link}. Starting link must start with http:// or https://."
            )
    return value


def validate_browser_info(value):
    allowed_browsers = ["chrome", "firefox", "safari", "edge", "brave", "opera"]
    if not any(browser in value.lower() for browser in allowed_browsers):
        raise serializers.ValidationError(f"Unsupported browser detected: {value}")
    return value


def validate_export_type(value):
    allowed_export_types = ["csv", "pdf", "excel"]
    if not any(export_types in value.lower() for export_types in allowed_export_types):
        raise serializers.ValidationError(f"Unsupported export type detected: {value}")
    return value


class BaseSerializer(serializers.Serializer):
    starting_links = serializers.ListField(child=serializers.URLField(), required=True)
    json_filename = serializers.CharField(required=False, max_length=100)
    browser_info = serializers.CharField(required=True)

    def validate_json_filename(self, value):
        return validate_json_filename(value)

    def validate_starting_links(self, value):
        return validate_starting_links(value)

    def validate_browser_info(self, value):
        return validate_browser_info(value)


class SearchTermSerializer(BaseSerializer):
    search_text = serializers.CharField(required=True)

    def validate_search_text(self, value):
        return validate_search_text(value)


class BrokenLinksSerializer(BaseSerializer):
    pass


class ExportResultsSerializer(serializers.Serializer):
    search_results = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField(max_length=255)),
        required=True,
    )
    broken_links = serializers.ListField(child=serializers.URLField(), required=True)
    access_required_links = serializers.ListField(
        child=serializers.URLField(), required=True
    )
    export_type = serializers.ChoiceField(
        choices=["pdf", "excel", "csv"], required=True
    )

    def validate_search_results(self, value):
        if not all(isinstance(item, list) and len(item) == 2 for item in value):
            raise serializers.ValidationError(
                "Each search result must be a list containing two elements: search term and found URL."
            )
        return value

    def validate_export_type(self, value):
        return validate_export_type(value)
