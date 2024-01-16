# Image_Reconstruction_with_Autoencoders
 This repository explores the use of Autoencoders for reconstructing MNIST images. In this repo we see the model's dimensionality reduction capabilities to compress and represent the data efficiently while aiming for faithful reconstruction.

# Autoencoder Architecture : (briefing)
  1) Encoder :  Compresses the input data into a lower-dimensional representation.
  2) Bottleneck : The narrowest layer in the network, containing the most compressed representation of the input. Important feature extraction from the input data takes
                  place here.
  3) Decoder :  Reconstructs the original input data from the compressed representation and aims to generate an output that closely resembles the original input.

# Training : 
  The encoder and decoder are trained together to minimize reconstruction error.

Note: Latent space dimensions play a crucial role in shaping the Autoencoder's output. It acts as a memory canvas, where more dimensions provide ample space to capture intricate details, leading to a higher resemblance between the generated output and the original input
 
 
