from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from auth_app.utils import IsAdmin, IsNotFrozen
from auth_app.models import User
from .models import PaperWork
from .serializers import PaperWorkSerializer, PaperWorkStatusUpdateSerializer, PaperWorkDeadlineUpdateSerializer
from auth_app.serializers import UserSerializer
from api.models import Version
from django.conf import settings
import os
import zipfile
import base64
from django.http import FileResponse, Http404, JsonResponse

def _auth_from_query_token(request):
    token = getattr(request, "query_params", {}).get("token") or request.GET.get("token")
    if not token:
        return None
    try:
        decoded = AccessToken(token)
        user_id = decoded.get("user_id")
        if not user_id:
            return None
        User = get_user_model()
        user = User.objects.get(id=user_id)
        request.user = user
        return user
    except TokenError as e:
        print(f"Token authentication error: {e}")
        return None
    except get_user_model().DoesNotExist:
        return None
    except Exception as e:
        print(f"Unexpected token parse error: {e}")
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
@csrf_exempt
def create_user(request):
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
@csrf_exempt
def update_paperwork_deadline(request, id):
    
    paperwork = get_object_or_404(PaperWork, id=id)
    
    serializer = PaperWorkDeadlineUpdateSerializer(paperwork, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(PaperWorkSerializer(paperwork).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
@csrf_exempt
def update_user_status(request, username):
    
    user = get_object_or_404(User, username=username)
    
    if 'status' not in request.data:
        return Response({'error': 'Status field is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    status_value = request.data['status']
    if status_value not in dict(User.STATUS_CHOICES):
        return Response({'error': 'Invalid status value'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.status = status_value
    user.save()
    
    return Response(UserSerializer(user).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
@csrf_exempt
def assign_paperwork(request):
    
    serializer = PaperWorkSerializer(data=request.data)
    if serializer.is_valid():
        # Get the researcher
        researcher_id = serializer.validated_data.pop('researcher_id')
        researcher = get_object_or_404(User, id=researcher_id, role='RESEARCHER')
        
        # Create the paperwork
        paperwork = serializer.save(researcher=researcher)
        
        return Response(PaperWorkSerializer(paperwork).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def users_list(request):
    """Endpoint to list all users except admins in the system. Only accessible to admins."""
    users = User.objects.exclude(role='ADMIN')
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])  # was IsAuthenticated
@xframe_options_exempt            # allow rendering in <iframe>
def view_paperwork_file(request, paperwork_id, version_no, file_type):
    # 1) Try auth from ?token=...
    _auth_from_query_token(request)

    # 2) If still unauthenticated, reject (works for either header or query-token)
    if not request.user or not request.user.is_authenticated:
        return Response({'detail': 'Authentication credentials were not provided.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # Existing lookup
    try:
        version = Version.objects.get(
            paperwork__id=paperwork_id, version_no=version_no
        )
    except Version.DoesNotExist:
        raise Http404("Version not found")

    # 3) Object-level authorization: admin OR the assigned researcher
    is_admin = getattr(request.user, 'role', '').upper() == 'ADMIN'
    is_owner = getattr(version.paperwork, 'researcher_id', None) == getattr(request.user, 'id', None)
    if not (is_admin or is_owner):
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    # ... keep your existing file path logic below unchanged ...
    file_path = None
    storage_path = None
    if file_type == 'pdf':
        file_path = version.pdf_path
        storage_path = settings.PDF_STORAGE_PATH
    elif file_type == 'tex':
        file_path = version.latex_path
        storage_path = settings.LATEX_STORAGE_PATH
    elif file_type == 'zip':
        file_path = version.python_path
        storage_path = settings.PYTHON_STORAGE_PATH
    elif file_type == 'docx':
        file_path = version.docx_path
        storage_path = settings.DOCX_STORAGE_PATH
    else:
        return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

    if not file_path:
        raise Http404(f"{file_type.capitalize()} file not found for this version")

    filename = os.path.basename(file_path) if file_path else f"paper.{file_type}"
    version_str = f"v{version_no}"

    storage_full_path = os.path.join(
        settings.MEDIA_ROOT, storage_path, str(paperwork_id), version_str, filename
    )

    if os.path.exists(storage_full_path):
        response = FileResponse(open(storage_full_path, 'rb'))
        disposition = 'attachment' if request.GET.get('download') else 'inline'
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response

    direct_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(direct_path):
        response = FileResponse(open(direct_path, 'rb'))
        disposition = 'attachment' if request.GET.get('download') else 'inline'
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response

    print(f"Attempted paths:\n1. {storage_full_path}\n2. {direct_path}")
    raise Http404("File not found on server")

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_detail(request, user_id):
    """Endpoint to get a specific user by ID. Only accessible to admins."""
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])  # was [IsAuthenticated, IsAdmin]
@xframe_options_exempt            # allow rendering in <iframe>
def view_zip_contents(request, paperwork_id, version_no):
    # 1) Try auth from ?token=
    _auth_from_query_token(request)

    # 2) Require auth
    if not request.user or not request.user.is_authenticated:
        return Response({'detail': 'Authentication credentials were not provided.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # 3) If you want admin-only, keep this:
    # is_admin = getattr(request.user, 'role', '').upper() == 'ADMIN'
    # if not is_admin:
    #     return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    # OR: allow the researcher who owns this paperwork to view too
    try:
        version = Version.objects.get(
            paperwork__id=paperwork_id, version_no=version_no
        )
    except Version.DoesNotExist:
        raise Http404("Version not found")

    is_admin = getattr(request.user, 'role', '').upper() == 'ADMIN'
    is_owner = getattr(version.paperwork, 'researcher_id', None) == getattr(request.user, 'id', None)
    if not (is_admin or is_owner):
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    version_str = f"v{version_no}"
    zip_path = os.path.join(
        settings.MEDIA_ROOT,
        settings.PYTHON_STORAGE_PATH,
        str(paperwork_id),
        version_str,
        "code.zip"
    )

    if not os.path.exists(zip_path):
        raise Http404("ZIP file not found")

    contents = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            contents.append(name)

    return JsonResponse({"files": contents})

@api_view(['GET'])
@permission_classes([AllowAny])
@xframe_options_exempt
def view_zip_file_content(request, paperwork_id, version_no, file_path):
    # 1) Try auth from ?token=...
    _auth_from_query_token(request)

    # 2) If still unauthenticated, reject
    if not request.user or not request.user.is_authenticated:
        return Response({'detail': 'Authentication credentials were not provided.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # Existing lookup
    try:
        version = Version.objects.get(
            paperwork__id=paperwork_id, version_no=version_no
        )
    except Version.DoesNotExist:
        raise Http404("Version not found")

    # 3) Object-level authorization: admin OR the assigned researcher
    is_admin = getattr(request.user, 'role', '').upper() == 'ADMIN'
    is_owner = getattr(version.paperwork, 'researcher_id', None) == getattr(request.user, 'id', None)
    if not (is_admin or is_owner):
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    version_str = f"v{version_no}"
    zip_path = os.path.join(
        settings.MEDIA_ROOT,
        settings.PYTHON_STORAGE_PATH,
        str(paperwork_id),
        version_str,
        "code.zip"
    )

    if not os.path.exists(zip_path):
        raise Http404("ZIP file not found")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Check if the file exists in the ZIP
            if file_path not in z.namelist():
                return Response({'error': 'File not found in ZIP archive'}, status=status.HTTP_404_NOT_FOUND)
            
            # Determine content type based on file extension
            file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            content_type = 'text/plain'
            is_binary = False
            
            # Text-based files
            if file_extension in ['py']:
                content_type = 'text/x-python'
            elif file_extension in ['ipynb']:
                content_type = 'application/json'
            # Image files
            elif file_extension in ['png']:
                content_type = 'image/png'
                is_binary = True
            elif file_extension in ['jpg', 'jpeg']:
                content_type = 'image/jpeg'
                is_binary = True
            
            # Handle binary files (images)
            if is_binary:
                file_content = base64.b64encode(z.read(file_path)).decode('utf-8')
                return Response({
                    'content': file_content, 
                    'content_type': content_type,
                    'is_binary': True
                })
            else:
                # Handle text files
                file_content = z.read(file_path).decode('utf-8', errors='replace')
                return Response({
                    'content': file_content, 
                    'content_type': content_type,
                    'is_binary': False
                })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)