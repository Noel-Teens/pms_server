from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer
)
from .models import User
from django.db import transaction
from .serializers import FirebaseLoginSerializer
from .utils import IsAdmin
from rest_framework_simplejwt.tokens import RefreshToken
from firebase_admin import auth as firebase_auth
import auth_app.firebase_app
from django.utils.text import slugify

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

def _issue_tokens_for_user(user: User) -> dict:
    """Create SimpleJWT tokens and return the same response shape as your normal login."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": getattr(user, "role", None),
            "status": getattr(user, "status", None),
        },
    }

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def google_login(request):
    """
    Accepts a Firebase ID token from the client (Google sign-in),
    verifies it with Firebase Admin, upserts a local User, and
    returns SimpleJWT tokens.
    """
    serializer = FirebaseLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    id_token = serializer.validated_data["id_token"]

    # 1) Verify the Firebase ID token (raises if invalid/expired)
    try:
        decoded = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"detail": f"Invalid Firebase token: {str(e)}"}, status=status.HTTP_401_UNAUTHORIZED)

    # 2) Extract claims
    email = decoded.get("email")
    email_verified = decoded.get("email_verified", False)
    name = decoded.get("name") or ""
    uid = decoded.get("uid")
    sign_in_provider = (decoded.get("firebase") or {}).get("sign_in_provider")

    # Optional hard checks
    if sign_in_provider != "google.com":
        return Response({"detail": "Not a Google sign-in token."}, status=status.HTTP_400_BAD_REQUEST)
    if not email or not email_verified:
        return Response({"detail": "Email missing or not verified."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Upsert user in your DB
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        base_username = slugify(email.split("@")[0]) or (uid or "")[:8] or "user"
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            counter += 1
            username = f"{base_username}{counter}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=None,         # no local password; Google-only sign-in
            # set defaults if your User has extra fields:
            role="RESEARCHER",
            status="ACTIVE",
        )
        user.set_unusable_password()
        if " " in name:
            first, last = name.split(" ", 1)
            user.first_name, user.last_name = first, last
        else:
            user.first_name = name
        user.save()

    # 4) Optional gate (e.g., only ACTIVE users)
    if getattr(user, "status", "ACTIVE") != "ACTIVE":
        return Response({"detail": f"Account {user.status}."}, status=status.HTTP_403_FORBIDDEN)

    # 5) Mint SimpleJWT tokens and return
    return Response(_issue_tokens_for_user(user), status=status.HTTP_200_OK)
