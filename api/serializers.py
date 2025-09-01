from rest_framework import serializers
from .models import Version, Notification, Review
from admin_app.models import PaperWork
from admin_app.serializers import PaperWorkSerializer

class VersionSerializer(serializers.ModelSerializer):
    paperwork = PaperWorkSerializer(read_only=True)
    
    class Meta:
        model = Version
        fields = ['id', 'paperwork', 'version_no', 'submitted_at', 'pdf_path', 
                  'latex_path', 'python_path', 'docx_path', 'ai_percent_self', 'ai_percent_verified']
        read_only_fields = ['id', 'submitted_at']

class VersionCreateSerializer(serializers.ModelSerializer):
    paperwork_id = serializers.UUIDField(write_only=True, required=False)
    paper_pdf = serializers.FileField(required=True)
    latex_tex = serializers.FileField(required=True)
    python_zip = serializers.FileField(required=True)
    docx_file = serializers.FileField(required=False)
    
    class Meta:
        model = Version
        fields = ['paperwork_id', 'version_no', 'paper_pdf', 'latex_tex', 'python_zip', 'docx_file',
                  'ai_percent_self', 'ai_percent_verified']
        read_only_fields = ['pdf_path', 'latex_path', 'python_path', 'docx_path']
    
    def create(self, validated_data):
        # File fields will be handled in the view
        paper_pdf = validated_data.pop('paper_pdf', None)
        latex_tex = validated_data.pop('latex_tex', None)
        python_zip = validated_data.pop('python_zip', None)
        docx_file = validated_data.pop('docx_file', None)
        
        # Create version instance without file paths
        version = Version.objects.create(**validated_data)
        
        return version

class NotificationSerializer(serializers.ModelSerializer):
    paper = PaperWorkSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'event', 'paper', 'at']
        read_only_fields = ['id', 'at']

class ReviewModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'paperwork', 'status', 'comments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ('ASSIGNED', 'Assigned'),
        ('SUBMITTED', 'Submitted'),
        ('CHANGES_REQUESTED', 'Changes Requested'),
        ('APPROVED', 'Approved'),
    ])
    comments = serializers.CharField(required=False, allow_blank=True)

class ReportSummarySerializer(serializers.Serializer):
    total_papers = serializers.IntegerField()
    papers_by_status = serializers.DictField(child=serializers.IntegerField())
    papers_by_researcher = serializers.DictField(child=serializers.IntegerField())
    average_ai_percentage = serializers.FloatField()

class ResearcherStatsSerializer(serializers.Serializer):
    total_paperwork = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    approved = serializers.IntegerField()
    changes_requested = serializers.IntegerField()

class AdminStatsSerializer(serializers.Serializer):
    total_paperwork = serializers.IntegerField()
    submitted = serializers.IntegerField()
    approved = serializers.IntegerField()
    changes_requested = serializers.IntegerField()