# Image preprocessing pipeline

import numpy as np
import cv2

class image_preprocessor:

    def __init__(self, target_size =(512, 512)):
        self.target_size = target_size

    def preprocess_single(self, img):
        img_resize = cv2.resize(img, self.target_size, interpolation=cv2.INTER_AREA)

        img_greyed = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)

        img_processed = np.expand_dims(img_greyed, axis=-1)

        img_final = img_processed.astype(np.float32) / 255

        return img_final
    
# to use
# preprocessor = image_preprocessor(target_size=(512, 512))
# pi_img = cv2.imread('im_capture.jpg')
# processed = preprocessor.preprocess_single(pi_img)
