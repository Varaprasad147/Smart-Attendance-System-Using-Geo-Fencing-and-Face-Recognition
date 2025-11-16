"""
FastAPI service for face recognition.
"""

import os
import uuid
import face_recognition
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime

app = FastAPI(
    title="Face Recognition Service",
    description="AI-powered face recognition service for attendance system",
    version="1.0.0"
)

# In-memory storage for face encodings (in production, use database)
face_encodings = {}

class FaceEnrollRequest(BaseModel):
    student_id: str
    encoding: list

class FaceVerifyRequest(BaseModel):
    student_id: str
    encoding: list

class FaceResponse(BaseModel):
    success: bool
    message: str
    matched: Optional[bool] = None
    distance: Optional[float] = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Face Recognition Service is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify service is working."""
    return {"message": "Face service is working", "face_recognition_available": True}

@app.post("/face/enroll", response_model=FaceResponse)
async def enroll_face(
    student_id: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Enroll a new face for a student.
    
    Args:
        student_id: Unique identifier for the student
        image: Face image file (JPEG/PNG)
    
    Returns:
        Success status and enrollment confirmation
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await image.read()
        
        # Load image using face_recognition from bytes
        import io
        from PIL import Image
        pil_image = Image.open(io.BytesIO(image_data))
        face_image = np.array(pil_image)
        
        # Detect face locations
        face_locations = face_recognition.face_locations(face_image)
        
        if not face_locations:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        if len(face_locations) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please use an image with only one face.")
        
        # Generate face encoding
        face_encoding = face_recognition.face_encodings(face_image, face_locations)[0]
        
        # Store encoding (in production, save to database)
        face_encodings[student_id] = {
            'encoding': face_encoding.tolist(),
            'enrolled_at': datetime.now().isoformat()
        }
        
        return FaceResponse(
            success=True,
            message=f"Face enrolled successfully for student {student_id}"
        )
        
    except Exception as e:
        print(f"Face enrollment error: {str(e)}")
        return FaceResponse(
            success=False,
            message=f"Face enrollment failed: {str(e)}"
        )

@app.post("/face/verify", response_model=FaceResponse)
async def verify_face(
    student_id: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Verify a face against enrolled face.
    
    Args:
        student_id: Unique identifier for the student
        image: Face image file to verify (JPEG/PNG)
    
    Returns:
        Verification result with match status and distance
    """
    try:
        # Check if student is enrolled
        if student_id not in face_encodings:
            raise HTTPException(status_code=404, detail="Student face not enrolled")
        
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await image.read()
        
        # Load image using face_recognition from bytes
        import io
        from PIL import Image
        pil_image = Image.open(io.BytesIO(image_data))
        face_image = np.array(pil_image)
        
        # Detect face locations
        face_locations = face_recognition.face_locations(face_image)
        
        if not face_locations:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        if len(face_locations) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please use an image with only one face.")
        
        # Generate face encoding for verification
        verify_encoding = face_recognition.face_encodings(face_image, face_locations)[0]
        
        # Get enrolled encoding
        enrolled_encoding = np.array(face_encodings[student_id]['encoding'])
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([enrolled_encoding], verify_encoding)[0]
        
        # Determine match (threshold: 0.6)
        threshold = 0.6
        matched = face_distance <= threshold
        
        return FaceResponse(
            success=True,
            message="Face verification completed",
            matched=matched,
            distance=float(face_distance)
        )
        
    except Exception as e:
        print(f"Face verification error: {str(e)}")
        return FaceResponse(
            success=False,
            message=f"Face verification failed: {str(e)}"
        )

@app.get("/face/status/{student_id}")
async def get_face_status(student_id: str):
    """
    Get enrollment status for a student.
    
    Args:
        student_id: Unique identifier for the student
    
    Returns:
        Enrollment status and details
    """
    if student_id in face_encodings:
        return {
            "enrolled": True,
            "enrolled_at": face_encodings[student_id]['enrolled_at']
        }
    else:
        return {"enrolled": False}

@app.delete("/face/remove/{student_id}")
async def remove_face(student_id: str):
    """
    Remove enrolled face for a student.
    
    Args:
        student_id: Unique identifier for the student
    
    Returns:
        Removal confirmation
    """
    if student_id in face_encodings:
        del face_encodings[student_id]
        return {"message": f"Face removed for student {student_id}"}
    else:
        raise HTTPException(status_code=404, detail="Student face not found")

@app.get("/face/stats")
async def get_face_stats():
    """Get statistics about enrolled faces."""
    return {
        "total_enrolled": len(face_encodings),
        "enrolled_students": list(face_encodings.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
