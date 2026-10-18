import subprocess
from datetime import datetime
import cv2

class Picamera:
	def capture_load(self):
		output_file = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

		subprocess.run([
    			'rpicam-still',
    			'-o', output_file,
    			'-t', '1',
    			'--width', '2592',
    			'--height', '1944'
				])

		print(f"Image saved: {output_file}")

		image = cv2.imread(output_file)
		print(f"Image shape: {image.shape}")
		
		return image, output_file

if __name__ == "__main__":
	camera = Picamera()
	image, filename = camera.capture_load()
