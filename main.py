from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
import uvicorn

app = FastAPI()

def process_frame(image: np.ndarray) -> int:
    """Process the image and return the vehicle count."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Use a simple edge detection for demonstration (Replace with ML model)
    edges = cv2.Canny(gray, 50, 150)
    
    # Dummy vehicle detection logic (Replace with real model)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    vehicle_count = len(contours)  # Simplified counting
    
    return vehicle_count

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint to receive video frames and process them."""
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if image is None:
        return {"error": "Invalid image format"}
    
    vehicle_count = process_frame(image)
    return {"vehicles_detected": vehicle_count}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
