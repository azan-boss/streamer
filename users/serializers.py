from rest_framework import serializers
from .models import User, ROLES
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

# If needed elsewhere in the file
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    role = serializers.ChoiceField(choices=ROLES.choices, default=ROLES.Viewer)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "role"
        ]

    def validate(self, data):
        # Check if passwords match
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # Prevent regular registration from creating admin users
        if data.get("role") == ROLES.Admin:
            # Check if request is from admin user
            request = self.context.get("request")
            if not (
                request
                and request.user
                and request.user.is_authenticated
                and request.user.role == ROLES.Admin
            ):
                raise serializers.ValidationError(
                    {"role": "You cannot create an admin user."}
                )

        return data

    def create(self, validated_data):
        # Remove confirm_password from the data
        validated_data.pop("confirm_password")
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)


import pyotp
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers
from django.contrib.auth import get_user_model


class TOTPSetupSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    otp_secret = serializers.CharField(read_only=True)
    qr_code_url = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Get the user by username (use get() instead of filter())
        user = User.objects.get(username=validated_data["username"])

        # Generate a random secret key
        secret_key = pyotp.random_base32()

        # Create a TOTP device for the user
        device = TOTPDevice.objects.create(
            user=user,
            name="Google Authenticator",
            confirmed=False,  # Not confirmed until user verifies
            key=secret_key,
        )

        # Generate provisioning URI (QR code URL)
        totp = pyotp.TOTP(secret_key)
        qr_code_url = totp.provisioning_uri(
            name=user.username, issuer_name="YourAppName"
        )

        # Return data for frontend to display
        return {"otp_secret": secret_key, "qr_code_url": qr_code_url}

    def validate(self, attrs):
        # Ensure the username exists
        try:
            User.objects.get(username=attrs["username"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return attrs


class TOTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp_code = serializers.CharField()

    def validate(self, attrs):
        try:
            # Get the user
            user = User.objects.get(username=attrs["username"])

            # Find the user's TOTP device
            device = TOTPDevice.objects.get(user=user, name="Google Authenticator")

            # Verify the OTP code
            totp = pyotp.TOTP(device.key)
            is_valid = totp.verify(attrs["otp_code"])

            if not is_valid:
                raise serializers.ValidationError({"otp_code": "Invalid OTP code"})

            # Mark the device as confirmed
            device.confirmed = True
            device.save()

            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User not found"})
        except TOTPDevice.DoesNotExist:
            raise serializers.ValidationError(
                {"device": "No TOTP device found for this user"}
            )
