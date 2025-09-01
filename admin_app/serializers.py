from rest_framework import serializers
from .models import PaperWork
from auth_app.serializers import UserSerializer

class PaperWorkSerializer(serializers.ModelSerializer):
    researcher = UserSerializer(read_only=True)
    researcher_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = PaperWork
        fields = ['id', 'title', 'researcher', 'researcher_id', 'status', 'assigned_at', 'deadline', 'updated_at']
        read_only_fields = ['id', 'assigned_at', 'updated_at']
    
    def create(self, validated_data):
        return PaperWork.objects.create(**validated_data)

class PaperWorkStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperWork
        fields = ['status']

class PaperWorkDeadlineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperWork
        fields = ['deadline']