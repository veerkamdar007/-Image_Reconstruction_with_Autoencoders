import tensorflow as tf
import keras
import os
import pickle
from tensorflow.keras import Model 
from tensorflow.keras.layers import Input, Conv2D,ReLU,BatchNormalization,Flatten,Dense,Reshape,Conv2DTranspose,Activation
from tensorflow.keras import backend as K
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError,BinaryCrossentropy
import numpy as np

class Autoencoder:
    """
    AE is a deep convolutional archi with encoder and decoder components.
    """
    def __init__(self,input_shape,conv_filters,conv_kernels,conv_strides,latent_space_dim):
        # Latent space is the bottleneck in the arhitecture

        self.input_shape = input_shape
        self.conv_filters = conv_filters # [2,4,8]
        self.conv_kernels = conv_kernels # [3,5,3]
        self.conv_strides = conv_strides  # [1,2,2]
        self.latent_space_dim = latent_space_dim

        self.encoder = None
        self.decoder = None
        self.model = None

        self._num_conv_layers = len(conv_filters)
        self._shape_before_bottleneck = None
        self._model_input = None

        self._build()


    def summary(self):
        self.encoder.summary()
        self.decoder.summary()
        self.model.summary()
    
    def compile(self,learning_rate = 0.0001):
        optimizer = Adam(learning_rate = learning_rate)
        mse_loss = MeanSquaredError()
        bce = BinaryCrossentropy()
        self.model.compile(optimizer = optimizer , loss = mse_loss) #optimizer='adam'
    
    def train(self,x_train, batch_size , num_epochs):
        self.model.fit(x_train , 
                       x_train,
                       batch_size = batch_size ,
                       epochs = num_epochs ,
                       shuffle = True)

    def save(self,save_folder = "."):
        self._create_folder_if_it_doesnt_exist(save_folder)
        self._save_parameters(save_folder)
        self._save_weights(save_folder)
    
    def load_weights(self,weights_path):
        self.model.load_weights(weights_path)
    
    def reconstruct(self, images):
        latent_representations = self.encoder.predict(images)
        reconstructed_images = self.decoder.predict(latent_representations)
        return reconstructed_images, latent_representations
    
    @classmethod
    def load(cls,save_folder = "."):
        parameters_path = os.path.join(save_folder,"parameters.pkl")
        with open(parameters_path , "rb") as f:
            parameters = pickle.load(f)
        autoencoder = Autoencoder(*parameters)
        weights_path = os.path.join(save_folder, "weights.h5")
        autoencoder.load_weights(weights_path)

        return autoencoder


    def _create_folder_if_it_doesnt_exist(self,folder):
        if  not os.path.exists(folder):
            os.makedirs(folder)
        
    def _save_parameters(self,save_folder):
        parameters = [
            self.input_shape,
            self.conv_filters,
            self.conv_kernels, 
            self.conv_strides, 
            self.latent_space_dim
        ]
        save_path = os.path.join(save_folder, "parameters.pkl")
        with open(save_path , "wb") as f:
            pickle.dump(parameters, f)
    
    def _save_weights(self,save_folder):
        save_path = os.path.join(save_folder, "weights.h5")
        self.model.save_weights(save_path)


    def _build(self):
        self._build_encoder()
        self._build_decoder()
        self._build_autoencoder()

    def _build_autoencoder(self):
        model_input = self._model_input
        model_output = self.decoder(self.encoder(model_input))
        self.model = Model(model_input, model_output,name = "autoencoder")

    def _build_decoder(self):
        decoder_input = self._add_decoder_input()
        dense_layer = self._add_dense_layer(decoder_input)
        reshape_layer = self._add_reshape_layer(dense_layer)
        conv_transpose_layers = self._add_conv_transpose_layers(reshape_layer)
        decoder_output = self._add_decoder_output(conv_transpose_layers)
        self.decoder = Model(decoder_input, decoder_output,name = "decoder")
    
    def _add_decoder_input(self):
        return Input(shape=self.latent_space_dim, name = "decoder_input")
    
    def _add_dense_layer(self,decoder_input):
        num_neurons = np.prod(self._shape_before_bottleneck) # [1,2,4] -> 8, We use the prod function so that we get a number of the neurons and not a 1D array
        dense_layer = Dense(num_neurons,name= "decoder_dense")(decoder_input)
        return dense_layer
    
    def _add_reshape_layer(self,dense_layer):
        return Reshape(self._shape_before_bottleneck)(dense_layer)
    
    def _add_conv_transpose_layers(self,x):
        """Add conv transpose blocks"""
        # Loop through all the conv layers in reverse order and stop at the first layer 
        for layer_index in reversed(range(1,self._num_conv_layers)):
            # [1,2] -> [2,1]
            x = self._add_conv_transpose_layer(layer_index,x)
        return x

    def _add_conv_transpose_layer(self,layer_index,x):
        layer_num = self._num_conv_layers - layer_index
        conv_transpose_layer = Conv2DTranspose(
            filters = self.conv_filters[layer_index],
            kernel_size = self.conv_kernels[layer_index],
            strides = self.conv_strides[layer_index],
            padding = "same" ,
            name = f"decoder_conv_transpose_layer{layer_num}"
        )
        x = conv_transpose_layer(x)
        x = ReLU(name = f"decoder_relu_{layer_num}")(x)
        x = BatchNormalization(name = f"decoder_bn_{layer_num}")(x)
        return x 
    
    def _add_decoder_output(self, x):
        conv_transpose_layer = Conv2DTranspose(
            filters = 1,
            kernel_size = self.conv_kernels[0],
            strides = self.conv_strides[0],
            padding = "same" ,
            name = f"decoder_conv_transpose_layer{self._num_conv_layers}"
        )
        x = conv_transpose_layer(x)
        output_layer = Activation("sigmoid",name = "sigmoid_layer")(x)
        return output_layer


    def _build_encoder(self):
        encoder_input = self._add_encoder_input()
        conv_layers= self._add_conv_layers(encoder_input) 
        bottleneck= self._add_bottleneck(conv_layers)
        self._model_input = encoder_input
        self.encoder = Model(encoder_input, bottleneck , name = "encoder")

#1
    def _add_encoder_input(self):
        return Input(shape = self.input_shape,name = "encoder_input")

#2
    def _add_conv_layers(self,encoder_input):
        """Creates convolutions in blocks in encode"""
        x = encoder_input
        for layer_index in range(self._num_conv_layers):
            x = self._add_conv_layer(layer_index, x)
        return x
    
    def _add_conv_layer(self,layer_index,x):
        """Adds a convolutional block to a graph of layers,consisting 
        of conv 2D + ReLU + batch normalization"""

        layer_number = layer_index + 1 # So that are numbering of layers starts at 1
        conv_layer = Conv2D(
            filters = self.conv_filters[layer_index],
            kernel_size = self.conv_kernels[layer_index],
            strides = self.conv_strides[layer_index],
            padding = "same",
            name = f"encoder_conv_layer_{layer_number}"
        )

        x = conv_layer(x)
        x = ReLU(name = f"encoder_relu_{layer_number}")(x)
        x= BatchNormalization(name = f"encoder_bn_{layer_number}")(x)
        return x
    
#3  

    def _add_bottleneck(self,x):
        """Flatten data and add bottleneck (Dense Layer)"""

        self._shape_before_bottleneck = K.int_shape(x)[1:] # This is going to be helpful while building the decoder. imp because we would know the shape of the data before it goes in the bottleneck network
        x = Flatten()(x)
        x = Dense(self.latent_space_dim,name = "encoder_output")(x)
        return x


if __name__ == "__main__":
    autoencoder = Autoencoder(
        input_shape = (28,28,1),
        conv_filters = (32,64,64,64),
        conv_kernels = (3,3,3,3),
        conv_strides = (1,2,2,1),
        latent_space_dim = 3000
    )

    autoencoder.summary()
