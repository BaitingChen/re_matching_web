from django.urls import path
from . import views

urlpatterns = [
    path('upload/',views.upload_file, name='upload_file'),
    path('files/<uuid:file_id>/preview/',views.get_file_preview, name='file_preview'),
    path('process/',views.process_pattern_matching,name='process_pattern'),
    path('jobs/<uuid:job_id>/',views.get_processing_job,name='get_job')
]
