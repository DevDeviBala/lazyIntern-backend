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
        
        # Reset link
        reset_link = f"http://localhost:3000/reset-password/{token}"
        
        subject = "Password Reset Request"
        message = f"""
        Hello {user.first_name},
        
        You requested a password reset for your LazyIntern account.
        
        Please click the following link to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        The LazyIntern Team
        """
        
        from_email = "LazyIntern <noreply@lazyintern.com>"
        
        send_mail(
            subject,
            message,
            from_email, 
            [user.email],
            fail_silently=False,
        )
        
        return Response({
            "message": "Password reset email sent"
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({"message": "If this email exists, a reset link has been sent"}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error sending email: {e}")
        return Response(
            {"detail": "Error sending email. Please try again later."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    
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