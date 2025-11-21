import base64
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time

# Load config from environment variables
cloudinary.config(
    cloud_name="djkyys3rt",
    api_key="733956983969816",
    api_secret="dMcdP4WkZWfkL8auqtChwXIo0vo"
)


def upload_image_to_cloudinary(image_base64: str, panel_id: str, filename: str = None) -> str:
    """
    Upload base64 image to Cloudinary.
    Returns the public URL.
    """

    try:
        # Remove "data:image/jpeg;base64," prefix if it exists
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        # Decode base64
        image_bytes = base64.b64decode(image_base64)

        # Use custom filename or auto
        public_id = filename or f"panel_{panel_id}_{int(time.time())}"

        upload_result = cloudinary.uploader.upload(
            image_bytes,
            folder="smart-solar-panel-cleaner",
            public_id=public_id,
            resource_type="image"
        )

        return upload_result.get("secure_url")

    except Exception as e:
        raise RuntimeError(f"Cloudinary upload failed: {str(e)}")
