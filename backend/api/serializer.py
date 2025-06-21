from rest_framework import serializers
from .models import FileUpload, ProcessingJob

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['id','filename','upload_date','file_type']

class ProcessingJobSerializer(serializers.ModelSerializer):
    file_upload = FileUploadSerializer(read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'file_upload', 'natural_language_query',
            'generated_regex', 'replacement_value', 'target_column',
            'status','created_at','completed_at','error_message'
        ]

class PatternMatchingRequestSerializer(serializers.Serializer):
    file_id = serializers.UUIDField()
    natural_language_query = serializers.CharField(max_length=1000)
    replacement_value = serializers.CharField(max_length=500)
    target_column = serializers.CharField(max_length=255, required=False, allow_blank=True)
