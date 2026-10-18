# TOM

## TOM_Exploratory_Work.ipynb
This notebook contains an attempt at developing TOM, using a Temporal Convolutional Network (TCN)
- Within this notebook, the model architecture is defined, simulated flight data is generated, a windowing function is made for use with the TCN, the model is trained and evaluated.
- A severe mistake was made in this work - the data was normalised using a scaler, which should have been fitted **only to the training data**. However, this scaler was fit to the entire dataset. This is referred to as data leakage, something this attempt at developing TOM was long expected to be suffering from, although the specific cause was only found recently.
- As such, the overly optimistic results produced by this model are not a true reflection of the models ability. This is made even worse by the fact the model failed completely when this testing was extended to any longer meaningful lengths.
- Thus, this attempt at TOM was a total failure, other than the learning opportunity presented for TCNs and dead recknoning.
- **Note**: GenAI was utilised in the development and research for TOM, in accordance with level 2X from the AI usage document on Brightspace. Please see the notebook for more detail.
