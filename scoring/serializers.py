from rest_framework import serializers


class SaveAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField()


class SubmitResultSerializer(serializers.Serializer):
    earned = serializers.IntegerField()
    total = serializers.IntegerField()
    correct = serializers.IntegerField()
