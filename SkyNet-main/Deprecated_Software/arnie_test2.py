#!/usr/bin/env python3
"""
SkyNet ARNIE Camera Test Script
Tests camera capture, image preprocessing, and ARNIE inference
Triggers: Every 2 minutes
"""

import time
import csv
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
import subprocess

import numpy as np
import cv2
from ai_edge_litert.interpreter import Interpreter

# Test configuration
TIME_TRIGGER = 120      # seconds (2 minutes for testing)

# Paths
IMAGE_DIR = Path('/home/tuppersat/skynet_data/images')
ARNIE_LOG = Path('/home/tuppersat/skynet_data/telem/arnie_test.csv')
MODEL_PATH = '/home/tuppersat/SkyNet/OBS/arnie_pure_tflite_0.06.tflite'

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
ARNIE_LOG.parent.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/tuppersat/logs/arnie_test.log')
    ]
)
logger = logging.getLogger('ARNIE_Test')


class ImagePreprocessor:
    """Image preprocessing pipeline for ARNIE"""
    
    def __init__(self, target_size=(512, 512)):
        self.target_size = target_size
        logger.info(f"ImagePreprocessor initialized: {target_size}")
    
    def preprocess_single(self, img):
        """
        Preprocess a single image for ARNIE inference
        
        Args:
            img: OpenCV image (BGR format)
            
        Returns:
            Preprocessed image ready for ARNIE (512x512, float32, normalized)
        """
        # Resize to target size
        img_resize = cv2.resize(img, self.target_size, interpolation=cv2.INTER_AREA)
        
        # Convert to grayscale
        img_greyed = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
        
        # Normalize to [0, 1] - 2D only, no extra dimensions
        img_final = img_greyed.astype(np.float32) / 255.0
        
        logger.info(f"Image preprocessed: shape={img_final.shape}, dtype={img_final.dtype}, range=[{img_final.min():.3f}, {img_final.max():.3f}]")
        
        return img_final


class PiCamera:
    """Raspberry Pi Camera interface"""
    
    def __init__(self, image_dir):
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"PiCamera initialized: {self.image_dir}")
    
    def capture(self, prefix='arnie_test'):
        """
        Capture image using rpicam-still
        
        Args:
            prefix: Filename prefix
            
        Returns:
            tuple: (opencv_image, filepath) or (None, None) on failure
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_file = self.image_dir / f"{prefix}_{timestamp}.jpg"
        
        try:
            # Capture image using rpicam-still
            subprocess.run([
                'rpicam-still',
                '-o', str(output_file),
                '-t', '1',
                '--width', '2592',
                '--height', '1944'
            ], check=True, timeout=10)
            
            logger.info(f"Image captured: {output_file.name}")
            
            # Load image with OpenCV
            image = cv2.imread(str(output_file))
            
            if image is None:
                logger.error(f"Failed to load captured image: {output_file}")
                return None, None
            
            logger.info(f"Image loaded: shape={image.shape}, dtype={image.dtype}")
            
            return image, str(output_file)
        
        except subprocess.TimeoutExpired:
            logger.error("Camera capture timeout")
            return None, None
        except subprocess.CalledProcessError as e:
            logger.error(f"Camera capture failed: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected camera error: {e}")
            return None, None


class ARNIEModel:
    """ARNIE TensorFlow Lite model interface"""
    
    def __init__(self, model_path):
        self.model_path = model_path
        
        try:
            # Load TFLite interpreter
            self.interpreter = Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            
            # Get input/output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            logger.info(f"ARNIE model loaded: {model_path}")
            logger.info(f"Input details: {self.input_details[0]}")
            logger.info(f"Output details: {self.output_details[0]}")
            
        except Exception as e:
            logger.error(f"ARNIE model loading failed: {e}")
            raise
    
    def infer(self, preprocessed_image):
        """
        Run ARNIE inference on preprocessed image
        
        Args:
            preprocessed_image: Preprocessed image (512x512, float32)
            
        Returns:
            dict: {'heading': float, 'raw_output': array, 'success': bool}
        """
        try:
            # Model expects 2D input (512, 512)
            input_data = np.expand_dims(preprocessed_image, axis=0)
            logger.info(f"Input data shape: {input_data.shape}, dtype={input_data.dtype}")
            
            # Set input tensor
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            
            # Run inference
            self.interpreter.invoke()
            
            # Get output
            output = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            logger.info(f"Raw output shape: {output.shape}, values: {output}")
            
            # Extract heading from output
            if output.shape == (2,) or (len(output.shape) == 1 and output.shape[0] == 2):
                # Sin/cos encoding
                sin_val = float(output[0])
                cos_val = float(output[1])
                heading = np.degrees(np.arctan2(sin_val, cos_val)) % 360
                logger.info(f"Sin/Cos encoding: sin={sin_val:.3f}, cos={cos_val:.3f}")
            elif output.shape == (1,) or (len(output.shape) == 1 and output.shape[0] == 1):
                # Direct angle output
                heading = float(output[0]) % 360
            elif len(output.shape) == 0:
                # Scalar
                heading = float(output) % 360
            else:
                # Flatten and take first value
                logger.warning(f"Unexpected output shape: {output.shape}, flattening")
                heading = float(output.flatten()[0]) % 360
            
            logger.info(f"ARNIE inference complete: heading={heading:.1f}°")
            
            return {
                'heading': heading,
                'raw_output': output,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"ARNIE inference error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'heading': 0.0,
                'raw_output': None,
                'success': False
            }


class ARNIETestSystem:
    """Complete ARNIE test system with camera and preprocessing"""
    
    def __init__(self):
        logger.info("Initializing ARNIE Test System...")
        
        # Initialize camera and ARNIE pipeline
        self.camera = PiCamera(IMAGE_DIR)
        self.preprocessor = ImagePreprocessor(target_size=(512, 512))
        self.arnie = ARNIEModel(MODEL_PATH)
        
        # Tracking variables
        self.last_trigger_time = time.time()
        self.image_count = 0
        
        # Create CSV log
        self._init_csv()
        
        logger.info("ARNIE Test System initialized successfully")
    
    def _init_csv(self):
        """Initialize ARNIE results CSV file"""
        with open(ARNIE_LOG, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp_utc',
                'image_id',
                'trigger_reason',
                'heading_deg',
                'inference_success',
                'image_path'
            ])
            f.flush()
        
        logger.info(f"ARNIE log created: {ARNIE_LOG}")
    
    def process_arnie_trigger(self):
        """Complete ARNIE processing pipeline"""
        logger.info("="*60)
        logger.info(f"ARNIE trigger: time_2min (image #{self.image_count + 1})")
        logger.info("="*60)
        
        # 1. Capture image
        image, image_path = self.camera.capture(prefix='arnie_test')
        
        if image is None:
            logger.error("Camera capture failed, skipping ARNIE processing")
            return
        
        # 2. Preprocess image
        try:
            preprocessed = self.preprocessor.preprocess_single(image)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return
        
        # 3. Run ARNIE inference
        result = self.arnie.infer(preprocessed)
        
        # 4. Log results
        timestamp = datetime.now(timezone.utc)
        self.image_count += 1
        
        with open(ARNIE_LOG, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                self.image_count,
                'time_2min',
                result['heading'],
                result['success'],
                image_path
            ])
            f.flush()
        
        logger.info(f"ARNIE result logged: heading={result['heading']:.1f}°")
        logger.info("="*60)
        
        # Update tracking
        self.last_trigger_time = time.time()
    
    def run_test(self, duration_minutes=10):
        """
        Run ARNIE test for specified duration
        
        Args:
            duration_minutes: How long to run the test
        """
        logger.info("="*60)
        logger.info(f"ARNIE TEST START - Duration: {duration_minutes} minutes")
        logger.info(f"Trigger: Every {TIME_TRIGGER} seconds ({TIME_TRIGGER/60:.1f} minutes)")
        logger.info("="*60)
        
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        
        try:
            while time.time() - start_time < duration_seconds:
                current_time = time.time()
                
                # Check if time trigger reached
                time_elapsed = current_time - self.last_trigger_time
                
                if time_elapsed >= TIME_TRIGGER:
                    self.process_arnie_trigger()
                
                # Status update every 30 seconds
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0 and elapsed > 0:
                    next_trigger = TIME_TRIGGER - int(time_elapsed)
                    logger.info(
                        f"Status: {elapsed}s elapsed | "
                        f"Images: {self.image_count} | "
                        f"Next trigger in: {next_trigger}s"
                    )
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
        
        except Exception as e:
            logger.error(f"Test error: {e}", exc_info=True)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("="*60)
        logger.info(f"Test complete: {self.image_count} images captured and processed")
        logger.info(f"Results saved to: {ARNIE_LOG}")
        logger.info(f"Images saved to: {IMAGE_DIR}")
        logger.info("="*60)


if __name__ == "__main__":
    # Run 10-minute test (will capture 5 images: 0min, 2min, 4min, 6min, 8min)
    test_system = ARNIETestSystem()
    test_system.run_test(duration_minutes=10)
