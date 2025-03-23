from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    TOTPSetupSerializer,
    TOTPVerifySerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from .authentication import CustomTokenObtainPairSerializer

# Get the custom User model
User = get_user_model()

# Create your views here.


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.save()

            # Create token data with user credentials
            token_data = {
                "username": user.username,
                "password": request.data["password"],
                "role": user.role,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }

            # Setup TOTP for the user
            totp_serializer = TOTPSetupSerializer(data={"username": user.username})
            totp_data = {}
            if totp_serializer.is_valid():
                totp_data = totp_serializer.save()

            # Generate tokens using CustomTokenObtainPairSerializer
            token_serializer = CustomTokenObtainPairSerializer(data=token_data)
            token_serializer.is_valid(raise_exception=True)
            tokens = token_serializer.validated_data

            return Response(
                {
                    "status": "success",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "permissions": list(user.get_all_permissions()),
                    },
                    "tokens": {
                        "refresh": tokens["refresh"],
                        "access": tokens["access"],
                    },
                    "totp": totp_data,  # Include TOTP setup data
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            user = authenticate(username=username, password=password)

            if user:
                user = User.objects.filter(username=username).first()
                tokenSerializer = CustomTokenObtainPairSerializer(user)
                return Response(
                    {
                        "status": "success",
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "role": user.role,  # Include role in response
                        },
                        "tokens": {
                            "refresh": str(tokenSerializer.validated_data["refresh"]),
                            "access": str(tokenSerializer.validated_data["access"]),
                        },
                    }
                )
            return Response(
                {"status": "error", "message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        return Response(
            {"status": "success", "message": "Logged out successfully"},
            status=status.HTTP_200_OK,
        )


class TOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TOTPVerifySerializer(data=request.data)
        print("hii iam here ")
        if serializer.is_valid():
            # OTP is valid, you can perform additional actions here
            return Response(
                {
                    "status": "success",
                    "message": "OTP verified successfully",
                    "is_2fa_enabled": True,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
