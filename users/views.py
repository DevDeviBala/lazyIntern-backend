from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import secrets
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken
from .serializers import RegisterSerializer


# ✅ Register view
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Login view
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")
    requested_role = request.data.get("role")  # Get role from request

    try:
        user = User.objects.get(email=email)
        
        # Optional: Validate role if provided
        if requested_role and user.role != requested_role:
            return Response(
                {"detail": "Invalid role for this account"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    except User.DoesNotExist:
        return Response({"detail": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(request, username=user.username, password=password)
    if not user:
        return Response({"detail": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "email": user.email,
        "role": user.role,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get("email")
    
    try:
        user = User.objects.get(email=email)
        
        # Delete any existing tokens
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=1)
        
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # For development: Print to console instead of sending email
        reset_link = f"http://localhost:3000/reset-password/{token}"
        print(f"Password reset link for {email}: {reset_link}")
        
        return Response({
            "message": "Password reset email sent",
            "reset_link": reset_link  # Include for development
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Don't reveal that email doesn't exist for security
        return Response({"message": "If this email exists, a reset link has been sent"}, status=status.HTTP_200_OK)
    
    
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request, token):
    new_password = request.data.get("password")
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            reset_token.delete()
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Delete the used token
        reset_token.delete()
        
        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        
    except PasswordResetToken.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)