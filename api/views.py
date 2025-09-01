from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from auth_app.utils import IsAdmin, IsNotFrozen
from django.db.models import Count, Avg
from django.http import HttpResponse
from django.conf import settings
import csv
import os

from auth_app.models import User
from admin_app.models import PaperWork
from .models import Version, Notification, Review
from .serializers import (
    VersionSerializer, VersionCreateSerializer, NotificationSerializer,
    ReviewSerializer, ReportSummarySerializer, ResearcherStatsSerializer,
    AdminStatsSerializer, ReviewModelSerializer
)
from admin_app.serializers import PaperWorkSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def paperworks_list(request):
    # Researchers can only see their own paperworks
    if request.user.role == 'RESEARCHER':
        paperworks = PaperWork.objects.filter(researcher=request.user)
    else:
        paperworks = PaperWork.objects.all()
    
    serializer = PaperWorkSerializer(paperworks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def paperwork_detail(request, id):
    paperwork = get_object_or_404(PaperWork, id=id)
    
    # Researchers can only see their own paperworks
    if request.user.role == 'RESEARCHER' and paperwork.researcher != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = PaperWorkSerializer(paperwork)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsNotFrozen])
@csrf_exempt
def versions_list(request, id):
    paperwork = get_object_or_404(PaperWork, id=id)
    
    # Researchers can only access their own paperworks
    if request.user.role == 'RESEARCHER' and paperwork.researcher != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        versions = Version.objects.filter(paperwork=paperwork)
        serializer = VersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Only researchers can submit versions
        if request.user.role != 'RESEARCHER' or paperwork.researcher != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the latest version number for this paperwork
        latest_version = Version.objects.filter(paperwork=paperwork).order_by('-version_no').first()
        next_version_no = 1 if not latest_version else latest_version.version_no + 1
        
        # Process the uploaded files
        serializer = VersionCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Handle file uploads
            paper_pdf = request.FILES.get('paper_pdf')
            latex_tex = request.FILES.get('latex_tex')
            python_zip = request.FILES.get('python_zip')
            docx_file = request.FILES.get('docx_file')
            
            # Create file paths
            paper_id = str(paperwork.id)
            version_str = f"v{next_version_no}"
            
            # Check if required files are provided
            if not paper_pdf or not latex_tex or not python_zip:
                return Response({'error': 'PDF, LaTeX, and Python ZIP files are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Save files to media storage
            pdf_path = None
            latex_path = None
            python_path = None
            docx_path = None
            
            # Create directory structures if they don't exist
            pdf_folder = os.path.join(settings.PDF_STORAGE_PATH, paper_id, version_str)
            latex_folder = os.path.join(settings.LATEX_STORAGE_PATH, paper_id, version_str)
            python_folder = os.path.join(settings.PYTHON_STORAGE_PATH, paper_id, version_str)
            docx_folder = os.path.join(settings.DOCX_STORAGE_PATH, paper_id, version_str)
            
            # Ensure all directories exist
            for folder in [pdf_folder, latex_folder, python_folder, docx_folder]:
                full_path = os.path.join(settings.MEDIA_ROOT, folder)
                os.makedirs(full_path, exist_ok=True)
            
            if paper_pdf:
                pdf_path = f"{pdf_folder}/paper.pdf"
                full_pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
                with open(full_pdf_path, 'wb+') as destination:
                    for chunk in paper_pdf.chunks():
                        destination.write(chunk)
            
            if latex_tex:
                latex_path = f"{latex_folder}/latex.tex"
                full_latex_path = os.path.join(settings.MEDIA_ROOT, latex_path)
                with open(full_latex_path, 'wb+') as destination:
                    for chunk in latex_tex.chunks():
                        destination.write(chunk)
            
            if python_zip:
                python_path = f"{python_folder}/code.zip"
                full_python_path = os.path.join(settings.MEDIA_ROOT, python_path)
                with open(full_python_path, 'wb+') as destination:
                    for chunk in python_zip.chunks():
                        destination.write(chunk)
            
            if docx_file:
                docx_path = f"{docx_folder}/paper.docx"
                full_docx_path = os.path.join(settings.MEDIA_ROOT, docx_path)
                with open(full_docx_path, 'wb+') as destination:
                    for chunk in docx_file.chunks():
                        destination.write(chunk)
            
            # Create version with file paths
            version = Version.objects.create(
                paperwork=paperwork,
                version_no=next_version_no,
                pdf_path=pdf_path,
                latex_path=latex_path,
                python_path=python_path,
                docx_path=docx_path,
                ai_percent_self=serializer.validated_data.get('ai_percent_self', 0.0)
            )
            
            # Update paperwork status
            paperwork.status = 'SUBMITTED'
            paperwork.save()
            
            # Check if there are more than 5 versions and delete the oldest ones
            versions = Version.objects.filter(paperwork=paperwork).order_by('-version_no')
            if versions.count() > 5:
                # Get versions to delete (all except the 5 most recent)
                versions_to_delete = versions[5:]
                
                for old_version in versions_to_delete:
                    # Delete files associated with this version
                    if old_version.pdf_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, old_version.pdf_path)):
                        os.remove(os.path.join(settings.MEDIA_ROOT, old_version.pdf_path))
                    
                    if old_version.latex_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, old_version.latex_path)):
                        os.remove(os.path.join(settings.MEDIA_ROOT, old_version.latex_path))
                    
                    if old_version.python_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, old_version.python_path)):
                        os.remove(os.path.join(settings.MEDIA_ROOT, old_version.python_path))
                    
                    if old_version.docx_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, old_version.docx_path)):
                        os.remove(os.path.join(settings.MEDIA_ROOT, old_version.docx_path))
                    
                    # Delete the version record
                    old_version.delete()
            
            # Create notification for new version
            Notification.objects.create(
                event='SUBMITTED',
                paper=paperwork
            )
            
            return Response(VersionSerializer(version).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def version_detail(request, id, ver):
    paperwork = get_object_or_404(PaperWork, id=id)
    
    # Researchers can only access their own paperworks
    if request.user.role == 'RESEARCHER' and paperwork.researcher != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    version = get_object_or_404(Version, paperwork=paperwork, version_no=ver)
    serializer = VersionSerializer(version)
    
    # Add full URLs for file downloads
    data = serializer.data
    if version.pdf_path:
        data['pdf_url'] = request.build_absolute_uri(settings.MEDIA_URL + version.pdf_path)
    if version.latex_path:
        data['latex_url'] = request.build_absolute_uri(settings.MEDIA_URL + version.latex_path)
    if version.python_path:
        data['python_url'] = request.build_absolute_uri(settings.MEDIA_URL + version.python_path)
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin, IsNotFrozen])
@csrf_exempt
def review_paperwork(request, id):
    
    paperwork = get_object_or_404(PaperWork, id=id)
    serializer = ReviewSerializer(data=request.data)
    
    if serializer.is_valid():
        # Update paperwork status
        paperwork.status = serializer.validated_data['status']
        paperwork.save()
        
        # Create or update review
        comments = serializer.validated_data.get('comments')
        if comments:
            Review.objects.create(
                status=paperwork.status,
                paperwork=paperwork,
                comments=comments
            )
        
        # Create notification for review
        Notification.objects.create(
            event='CHANGES_REQUESTED' if paperwork.status == 'CHANGES_REQUESTED' else 'APPROVED',
            paper=paperwork
        )
        
        return Response(PaperWorkSerializer(paperwork).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paperwork_reviews(request, id):
    paperwork = get_object_or_404(PaperWork, id=id)
    
    # Check if user is admin or the researcher who owns the paperwork
    if not (request.user.is_superuser or request.user == paperwork.researcher):
        return Response({"detail": "You do not have permission to view these reviews."}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    reviews = Review.objects.filter(paperwork=paperwork).order_by('-created_at')
    serializer = ReviewModelSerializer(reviews, many=True)
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin, IsNotFrozen])
def reports_summary(request):
    
    # Get total papers count
    total_papers = PaperWork.objects.count()
    
    # Get papers by status
    papers_by_status = PaperWork.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in papers_by_status}
    
    # Get papers by researcher
    papers_by_researcher = PaperWork.objects.values('researcher__username').annotate(count=Count('id'))
    researcher_dict = {item['researcher__username']: item['count'] for item in papers_by_researcher}
    
    # Get average AI percentage
    avg_ai_percent = Version.objects.aggregate(avg=Avg('ai_percent_verified'))['avg'] or 0
    
    data = {
        'total_papers': total_papers,
        'papers_by_status': status_dict,
        'papers_by_researcher': researcher_dict,
        'average_ai_percentage': avg_ai_percent
    }
    
    serializer = ReportSummarySerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin, IsNotFrozen])
def reports_export(request):
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="papers_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Researcher', 'Status', 'Assigned At', 'Latest Version', 'AI Percentage'])
    
    paperworks = PaperWork.objects.all()
    for paper in paperworks:
        # Get latest version if exists
        latest_version = Version.objects.filter(paperwork=paper).order_by('-version_no').first()
        version_no = latest_version.version_no if latest_version else 'N/A'
        ai_percent = latest_version.ai_percent_verified if latest_version else 'N/A'
        
        writer.writerow([
            paper.id,
            paper.title,
            paper.researcher.username,
            paper.status,
            paper.assigned_at.strftime('%Y-%m-%d'),
            version_no,
            ai_percent
        ])
    
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def notifications_list(request):
    # Get notifications relevant to the user
    if request.user.role == 'RESEARCHER':
        # Researchers only see notifications for their papers
        notifications = Notification.objects.filter(paper__researcher=request.user).order_by('-at')
    else:
        # Admins see all notifications
        notifications = Notification.objects.all().order_by('-at')
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def researcher_stats(request):
    # Only researchers can access their own stats
    if request.user.role != 'RESEARCHER':
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all paperworks for this researcher
    paperworks = PaperWork.objects.filter(researcher=request.user)
    
    # Calculate statistics
    total_paperwork = paperworks.count()
    pending_review = paperworks.filter(status='SUBMITTED').count()
    approved = paperworks.filter(status='APPROVED').count()
    changes_requested = paperworks.filter(status='CHANGES_REQUESTED').count()
    
    data = {
        'total_paperwork': total_paperwork,
        'pending_review': pending_review,
        'approved': approved,
        'changes_requested': changes_requested
    }
    
    serializer = ResearcherStatsSerializer(data)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsNotFrozen])
def delete_paperwork(request, id):
    paperwork = get_object_or_404(PaperWork, id=id)
    
    # Check permissions: Only admins or the researcher who owns the paperwork can delete it
    if request.user.role != 'ADMIN' and (request.user.role == 'RESEARCHER' and paperwork.researcher != request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all versions to delete associated files
    versions = Version.objects.filter(paperwork=paperwork)
    
    # Delete all files associated with this paperwork
    for version in versions:
        # Delete PDF file if exists
        if version.pdf_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, version.pdf_path)):
            os.remove(os.path.join(settings.MEDIA_ROOT, version.pdf_path))
        
        # Delete LaTeX file if exists
        if version.latex_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, version.latex_path)):
            os.remove(os.path.join(settings.MEDIA_ROOT, version.latex_path))
        
        # Delete Python ZIP file if exists
        if version.python_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, version.python_path)):
            os.remove(os.path.join(settings.MEDIA_ROOT, version.python_path))
        
        # Delete DOCX file if exists
        if version.docx_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, version.docx_path)):
            os.remove(os.path.join(settings.MEDIA_ROOT, version.docx_path))
    
    # Delete the paperwork (this will cascade delete versions and notifications)
    paperwork.delete()
    
    return Response({'message': 'Research task deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin, IsNotFrozen])
def admin_stats(request):
    # Only admins can access these stats
    
    # Get all paperworks
    paperworks = PaperWork.objects.all()
    
    # Calculate statistics
    total_paperwork = paperworks.count()
    submitted = paperworks.filter(status='SUBMITTED').count()
    approved = paperworks.filter(status='APPROVED').count()
    changes_requested = paperworks.filter(status='CHANGES_REQUESTED').count()
    
    data = {
        'total_paperwork': total_paperwork,
        'submitted': submitted,
        'approved': approved,
        'changes_requested': changes_requested
    }
    
    serializer = AdminStatsSerializer(data)
    return Response(serializer.data)