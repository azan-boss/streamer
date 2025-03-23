import pyotp
import uuid
from datetime import datetime, timedelta
from .models import OTPService


def get_device_id(request):
    """Generate or retrieve a device ID from the request"""
    # In a real implementation, you might get this from a header/cookie
    # or generate based on device fingerprinting
    return str(uuid.uuid4())


def generate_otp(user, device_id):
    """Generate a new OTP for the given user and device"""
    # Create or get the OTP service record for this user and device
    otp_service, created = OTPService.objects.get_or_create(
        user=user, device_id=device_id, defaults={"secret_key": pyotp.random_base32()}
    )

    # Create a TOTP object
    totp = pyotp.TOTP(otp_service.secret_key, interval=300)  # 5-minute validity

    # Generate the OTP
    otp = totp.now()

    # Update the last_used timestamp
    otp_service.last_used = datetime.now()
    otp_service.save()

    return otp


def verify_otp(user, device_id, otp):
    """Verify the OTP for the given user and device"""
    try:
        # Get the OTP service record
        otp_service = OTPService.objects.get(
            user=user, device_id=device_id, is_active=True
        )

        # Create a TOTP object
        totp = pyotp.TOTP(otp_service.secret_key, interval=300)  # 5-minute validity

        # Verify OTP
        is_valid = totp.verify(otp)

        if is_valid:
            # Update the last_used timestamp
            otp_service.last_used = datetime.now()
            otp_service.save()

        return is_valid
    except OTPService.DoesNotExist:
        return False
