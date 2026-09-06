from rest_framework import serializers


class ExplainSerializer(serializers.Serializer):
    html = serializers.CharField()
