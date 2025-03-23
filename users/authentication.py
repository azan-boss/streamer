from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .utils import generate_otp, verify_otp, get_device_id
from enum import Enum


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["user_id"] = str(user.id)
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser
        token["permissions"] = list(user.get_all_permissions())
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra responses along with tokens
        user = self.user
        data.update(
            {
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "permissions": list(user.get_all_permissions()),
                "role": user.role,
            }
        )

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False)


class OTPVerificationSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()
    device_id = serializers.CharField()


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(username=serializer.validated_data["username"])
            if not user.check_password(serializer.validated_data["password"]):
                raise User.DoesNotExist
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        device_id = serializer.validated_data.get("device_id") or get_device_id(request)
        otp = generate_otp(user, device_id)

        # In production, send OTP via SMS/Email instead of returning it
        return Response(
            {
                "message": "OTP sent successfully",
                "device_id": device_id,
                "otp": otp,  # Remove in production
            }
        )


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(username=serializer.validated_data["username"])
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if verify_otp(
            user,
            serializer.validated_data["device_id"],
            serializer.validated_data["otp"],
        ):
            # Generate JWT token
            token_serializer = CustomTokenObtainPairSerializer()
            token = token_serializer.get_token(user)

            return Response(
                {
                    "access": str(token.access_token),
                    "refresh": str(token),
                    "role": user.role,
                    "permissions": user.get_group_permissions(),
                }
            )

        return Response({"error": "Invalid OTP"}, status=status.HTTP_401_UNAUTHORIZED)
