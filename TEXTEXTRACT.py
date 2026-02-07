import cv2
import pytesseract
from PIL import Image
import tkinter as tk
from tkinter import filedialog

# Set Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Function to get image file from user
def get_image():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title="Select an Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    return file_path

# Ask user to select an image
image_path = get_image()

if image_path:
    # Read the image
    image = cv2.imread(image_path)

    # Convert image to grayscale for better OCR accuracy
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding (optional, improves accuracy for some images)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Save processed image temporarily
    cv2.imwrite("processed_image.png", gray)

    # Extract text using Tesseract OCR
    text = pytesseract.image_to_string(Image.open("processed_image.png"))

    # Print extracted text
    print("\nExtracted Text:\n", text)

else:
    print("No image selected.")





 