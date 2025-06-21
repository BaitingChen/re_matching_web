import os
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.conf import settings
from .models import FileUpload, ProcessingJob
from .serializer import (FileUploadSerializer,
                         ProcessingJobSerializer,
                         PatternMatchingRequestSerializer)
from .services import FileProcessingService
# Create your views here.
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    """handle file upload"""
    if 'file' not in request.FILES:
        return Response(
            {'error':'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    file = request.FILES['file']
    
    # validate file size
    if file.size > settings.MAX_FILE_SIZE:
        return Response(
            {'error':f'File size exceeds limit of {settings.MAX_FILE_SIZE/1024/1024}MB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # validate file type
    file_extension = os.path.splitext(file.name)[1].lower()
    allowed_extensions = ['.csv','.xlsx','.xls']
    if file_extension not in allowed_extensions:
        return Response(
            {'error':f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'},
            status = status.HTTP_400_BAD_REQUEST
        )
    
    # Determine file type
    file_type = 'csv' if file_extension == '.csv' else 'excel'

    try:
        # create file upload record
        file_upload = FileUpload.objects.create(
            file=file,
            filename=file.name,
            file_type=file_type
        )
        serializer = FileUploadSerializer(file_upload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error':f'Error uploading file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_file_preview(request, file_id):
    """Get preview of uploaded file"""
    try:
        file_upload = FileUpload.objects.get(id=file_id)
        service = FileProcessingService()
        
        df = service.read_file(file_upload)

        # Get preview data (first 10 rows)
        preview_data = df.head(10).to_dict('records')
        text_columns = service.get_text_columns(df)

        return Response({
            'preview_data':preview_data,
            'columns':list(df.columns),
            'text_columns':text_columns,
            'total_rows':len(df)
        })
    except FileUpload.DoesNotExist:
        return Response(
            {'error':'File not found'},
            status = status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error':f'Error reading file: {str(e)}'},
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def process_pattern_matching(request):
    """Process pattern matching and replacement"""

    serializer = PatternMatchingRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data=serializer.validated_data
    
    try:
        file_upload = FileUpload.objects.get(id=data['file_id'])

        # Create processing job
        job = ProcessingJob.objects.create(
            file_upload=file_upload,
            natural_language_query=data['natural_language_query'],
            replacement_value=data['replacement_value'],
            target_column=data.get('target_column',''),
            status='processing'
        )

        # Process file
        service = FileProcessingService()
        result = service.process_file_with_pattern(
            file_upload,
            data['natural_language_query'],
            data['replacement_value'],
            data.get('target_column')
        )

        # Update job status
        if result['success']:
            job.generated_regex = result['regex_pattern']
            job.status = 'completed'
        else:
            job.status = 'failed'
            job.error_message = result['error']
        job.save()

        # Preapare response
        response_data = {
            'job_id': job.id,
            'status':job.status,
            **result
        }

        return Response(response_data)
    
    except FileUpload.DoesNotExist:
        return Response(
            {'error':'File not found'},
            status = status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error':f'Processing error:{str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET'])
def get_processing_job(request, job_id):
    """Get processing job status and results"""
    
    try:
        job = ProcessingJob.objects.get(id=job_id)
        serializer = ProcessingJobSerializer(job)
        return Response(serializer.data)
    except ProcessingJob.DoesNotExist:
        return Response(
            {'error':'Job not found'},
            status=status.HTTP_404_NOT_FOUND
        )