import qrcode
import base64
import os
from PySide6.QtGui import QPixmap
from qrcode.image.pure import PymagingImage  # Use a different image type

def generate_qr_image(data, output_path='qr_code.png'):
    """
    Generate a QR code image and save it to the specified path
    
    Args:
        data (str): Data to encode in the QR code
        output_path (str): Path to save the QR code image
        
    Returns:
        str: Path to the saved QR code image
    """
    try:
        # Try method 1: Standard QR code generation
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Use a simpler image format 
        img = qr.make_image(fill='black', back_color='white')
        img.save(output_path)
        
        # Verify that the file was created
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("QR code file was not created properly")
            
        return output_path
    except Exception as e:
        print(f"QR generation error (method 1): {str(e)}")
        try:
            # Fallback method 2: Use a different QR library approach
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Use the pure Python implementation instead
            img = qr.make_image(fill_color="black", back_color="white", image_factory=PymagingImage)
            with open(output_path, 'wb') as f:
                img.save(f)
                
            return output_path
        except Exception as e2:
            print(f"QR generation error (method 2): {str(e2)}")
            # If all else fails, return an empty path
            return ""

def get_pixmap_from_base64(base64_string):
    """
    Convert a base64 string to a QPixmap object
    
    Args:
        base64_string (str): Base64 encoded string
        
    Returns:
        QPixmap: QPixmap object created from the base64 string
    """
    try:
        image_data = base64.b64decode(base64_string)
        pixmap = QPixmap()
        success = pixmap.loadFromData(image_data)
        if not success or pixmap.isNull():
            raise Exception("Failed to load pixmap from data")
        return pixmap
    except Exception as e:
        print(f"Error loading pixmap from base64: {str(e)}")
        # Return an empty pixmap
        return QPixmap() 