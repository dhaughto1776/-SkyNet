# ARNIE - Attitude Recognition Neural Intelligence Engine

## Notes:
- Lab demonstrator **Caimin McKenna** was extremely helpful in getting ARNIE's data pipeline and training to work. He specifically provided invaluable help with making the images look realistic and comparable to the SkyNet onboard cameras output, the Monte Carlo cropping, which produced drastic improvements to the speed of the pipeline and the crops produced, as well as helping with the HSV water detection. Thank you Caimin!
- GenAI was utilised during development of ARNIE in accordance with level 2X for research. Specific usage cases are highlighted where relevant.

## Model_Versions
This folder contains different ARNIE model versions. Mnay versions were saved during training, as this was time consuming and losing a model would be catastrophic.

- **ARNIE_test.tflite:** A toy model, built early and quite different from the final version of ARNIE, to verify that the model could operate on a Pi Zero 2

- The below models are 'flight ready' versions, bot not the final flight version. The numbers in their name indicate the final loss metric achieved (i.e., arnie_pure_tflite_02.tflite reached loss of 0.2, was saved and exported, before trained further)
- - 'arnie_pure_tflite_0.06.tflite'
- - 'arnie_pure_tflite_02.tflite'

- The below model is the **final version of ARNIE**, (which reached the same loss as arnie_pure_tflite_0.06.tflite, but was renamed)
- - **arnie_pure_tflite_FLIGHT.tflite**
 
## Training Data
This folder contains the tools needed to create ARNIE, the data generation pipeline, generation logs, and the model training notebook

- **arnie_genesis.ipynb**
- - This is the notebook in which ARNIE's architecture is built, the data is loaded in and batched, the model is trained on said data, and finally exported to tflite for Pi ZEero 2 deployment
  - **NOTE**: As stated in the notebook, to run this notebook in a reasonable time, a high ram GPU is needed. I used the T4 High Ram GPU, unfortunately access to this is not free.
 
- **Data Generation Log.txt**
- - A text file containing information on the datasets produced (including source image used, number of images produced, altitude range used, and size in mb or Gb)
 
- **Data_Set_Creation.ipynb**
- - The data generation pipeline. Instructions on usage can be seen below.

## How to operate the data generation pipeline - Data_Set_Creation.ipynb
- 1) Download notebook locally - DO NOT BOTHER RUNNING ON CLOUD
- 2) Load into vscode or similar
- 3) Get your high res image, preferably atmosphere corrected - make sure its sentinel 10m resolution image -.png or .jp2 work (.pngs load way quicker)
- 4) Go to the 'all_crops = [] ...' block, and change highlighted parameters if necessary
- 5) The images NEED TO HAVE WATER FEATURES. Visually inspect them to make sure most of them have some sort of coastline feature. The features are found using hsv (specifically Saturation and Value) and edge detection. The curretn setup works on most images, so the thresholds shouldn't need to be changed.
- 6) To verify sufficient water feature population in the images, run it and plot the images you get (only plot 5 to 10 at a time).
- 7) If majority of images produced have a mixture, go back and change the number of rotations performed. Do maybe 40 crops, and 50 rotations - this will take a while
- 8) Inspect images again, if they look good, download .npz file and upload to ARNIE training data/DATASETS folder on the drive. Upload the image used to the KEEPS folder.
- 9) Number of images = alts * crops * rots - 4 alts, 50 crops, 40 rots -> 8000 images ~ 1.2 Gb

**WARNING:** This pipeline is very intensive computationally, due to the sentinel image size. In my experience, my laptop could not handle runming this pipeline and doing other stuff simultaneously. But its also a geriatric laptop. Just something to keep in mind.

