import os
import logging
from flask import Flask, render_template, Response
from picamera2 import Picamera2
import cv2
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Picamera2 instance
camera = None
camera_initialized = False

# Initialize camera only once to avoid errors
def initialize_camera():
    global camera, camera_initialized
    if not camera_initialized:
        try:
            camera = Picamera2()
            camera.configure("preview")
            config = camera.create_preview_configuration(
                main={"size": (1280, 1024)}  # Set desired resolution (e.g., 1280x720)
            )
            # Set manual exposure time and disable auto exposure
            camera.set_controls({
                "ExposureTime": 20000,  # 20 ms exposure
                "AeEnable": True      # Disable auto exposure
            })

            camera.start()
            camera_initialized = True
            logger.info("Camera initialized successfully with custom settings.")
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            camera_initialized = False

# Route for serving the video stream
@app.route('/video_feed')
def video_feed():
    logger.info("Video feed requested.")
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route for displaying the main page
@app.route('/')
def index():
    return render_template('index.html')

# Generate video frames for streaming
def generate_frames():
    global camera
    initialize_camera()  # Ensure camera is initialized

    if not camera_initialized:
        logger.error("Camera not initialized properly.")
        return

    try:
        while True:
            # Capture a frame
            frame = camera.capture_array()

            # Add timestamp to the frame
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_color = (128,128, 255)  # White color
            thickness = 2
            position = (frame.shape[1] - 300, frame.shape[0] - 20)  # Bottom-right corner

            cv2.putText(frame, timestamp, position, font, font_scale, font_color, thickness)

            # Convert the frame to JPEG
            success, jpeg = cv2.imencode('.jpg', frame)
            if not success:
                logger.error("Failed to encode frame.")
                continue

            # Yield the JPEG image as part of the multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

            # Limit frame rate
            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error during frame generation: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=False)

