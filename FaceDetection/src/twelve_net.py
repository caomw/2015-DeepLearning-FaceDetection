"""This tutorial introduces the LeNet5 neural network architecture
using Theano.  LeNet5 is a convolutional neural network, good for
classifying images. This tutorial shows how to build the architecture,
and comes with all the hyper-parameters you need to reproduce the
paper's MNIST results.


This implementation simplifies the model in the following ways:

 - LeNetConvPool doesn't implement location-specific gain and bias parameters
 - LeNetConvPool doesn't implement pooling by average, it implements pooling
   by max.
 - Digit classification is implemented with a logistic regression rather than
   an RBF network
 - LeNet5 was not fully-connected convolutions at second layer

References:
 - Y. LeCun, L. Bottou, Y. Bengio and P. Haffner:
   Gradient-Based Learning Applied to Document
   Recognition, Proceedings of the IEEE, 86(11):2278-2324, November 1998.
   http://yann.lecun.com/exdb/publis/pdf/lecun-98.pdf

"""
import os
import sys
import time

import numpy

import theano
import theano.tensor as T
from theano.tensor.signal import downsample
from theano.tensor.nnet import conv

from logistic_sgd import LogisticRegression, load_data
from mlp import HiddenLayer
from skimage.io.collection import ImageCollection, concatenate_images
from matplotlib.image import imread
from skimage.transform._warps import resize

class twelve_net():
    
    def __init__(self, input,batch_size):
        
        #layer0_input = x.reshape((batch_size, 3, 13, 13))
        rng = numpy.random.RandomState(23455)
        
        img_size=13
        img_channels =3
        
        conv_filter_size = 3
        conv_filter_stride =1 # hard coded
        conv_filter_depth = 16
        
        ## Not used becusee it is hardcoded  inside le-net
        pool_filter_size = 3
        pool_filter_stride = 2 
        
        conv_pool_output_size = 5 ## 10
        
        fullyconnected_output_size = 16
    
        self.conv_pool_layer = LeNetConvPoolLayer(
            rng,
            input=input,
            image_shape=(batch_size, img_channels, img_size, img_size),
            filter_shape=(conv_filter_depth, img_channels, conv_filter_size, conv_filter_size),
            poolsize=(3, 3)
        )
        
        
        
        self.fullyconnected_layer = HiddenLayer(
        rng,
        input=self.conv_pool_layer.output.flatten(2),
        n_in=conv_filter_depth * conv_pool_output_size * conv_pool_output_size,
        n_out=fullyconnected_output_size,
        activation=T.tanh
        )
    
     
        self.log_regression_layer = LogisticRegression(input=self.fullyconnected_layer.output, n_in=fullyconnected_output_size, n_out=2)
        
        self.params = self.conv_pool_layer.params + self.fullyconnected_layer.params +self.log_regression_layer.params
        
        
    
class LeNetConvPoolLayer(object):
    """Pool Layer of a convolutional network """

    def __init__(self, rng, input, filter_shape, image_shape, poolsize=(3, 3)):
        """
        Allocate a LeNetConvPoolLayer with shared variable internal parameters.

        :type rng: numpy.random.RandomState
        :param rng: a random number generator used to initialize weights

        :type input: theano.tensor.dtensor4
        :param input: symbolic image tensor, of shape image_shape

        :type filter_shape: tuple or list of length 4
        :param filter_shape: (number of filters, num input feature maps,
                              filter height, filter width)

        :type image_shape: tuple or list of length 4
        :param image_shape: (batch size, num input feature maps,
                             image height, image width)

        :type poolsize: tuple or list of length 2
        :param poolsize: the downsampling (pooling) factor (#rows, #cols)
        """

        assert image_shape[1] == filter_shape[1]
        self.input = input

        # there are "num input feature maps * filter height * filter width"
        # inputs to each hidden unit
        fan_in = numpy.prod(filter_shape[1:])
        # each unit in the lower layer receives a gradient from:
        # "num output feature maps * filter height * filter width" /
        #   pooling size
        fan_out = (filter_shape[0] * numpy.prod(filter_shape[2:]) /
                   numpy.prod(poolsize))
        # initialize weights with random weights
        W_bound = numpy.sqrt(6. / (fan_in + fan_out))
        self.W = theano.shared(
            numpy.asarray(
                rng.uniform(low=-W_bound, high=W_bound, size=filter_shape),
                dtype=theano.config.floatX  # @UndefinedVariable
            ),
            borrow=True
        )

        # the bias is a 1D tensor -- one bias per output feature map
        b_values = numpy.zeros((filter_shape[0],), dtype=theano.config.floatX)  # @UndefinedVariable
        self.b = theano.shared(value=b_values, borrow=True) 

        conv_layer_stride = 1;
        # convolve input feature maps with filters
        conv_out = conv.conv2d(
            input=input,
            filters=self.W,
            filter_shape=filter_shape,
            image_shape=image_shape,
            subsample=(conv_layer_stride,conv_layer_stride)
        )

        # downsample each feature map individually, using maxpooling
        pooled_out = downsample.max_pool_2d(
            input=conv_out,
            ds=poolsize,
            ignore_border=True,
            st = (2,2)
        )

        # add the bias term. Since the bias is a vector (1D array), we first
        # reshape it to a tensor of shape (1, n_filters, 1, 1). Each bias will
        # thus be broadcasted across mini-batches and feature map
        # width & height
        self.output = T.tanh(pooled_out + self.b.dimshuffle('x', 0, 'x', 'x'))

        # store parameters of this layer
        self.params = [self.W, self.b]

def evaluate_12net(learning_rate=0.1, n_epochs=200,
                    dataset='mnist.pkl.gz',
                    nkerns=[20, 50], batch_size=2):
    """ Demonstrates lenet on MNIST dataset

    :type learning_rate: float
    :param learning_rate: learning rate used (factor for the stochastic
                          gradient)

    :type n_epochs: int
    :param n_epochs: maximal number of epochs to run the optimizer

    :type dataset: string
    :param dataset: path to the dataset used for training /testing (MNIST here)

    :type nkerns: list of ints
    :param nkerns: number of kernels on each layer
    """

    rng = numpy.random.RandomState(23455)

    

    train_set_x, train_set_y = get_test_data()


    # compute number of minibatches for training, validation and testing
    n_train_batches = train_set_x.get_value(borrow=True).shape[0]

    n_train_batches /= batch_size


    # allocate symbolic variables for the data
    index = T.lscalar()  # index to a [mini]batch

    # start-snippet-1
    x = T.matrix('x')   # the data is presented as rasterized images
    y = T.ivector('y')  # the labels are presented as 1D vector of
                        # [int] labels

    ######################
    # BUILD ACTUAL MODEL #
    ######################
    print '... building the model'

    # Reshape matrix of rasterized images of shape (batch_size, 28 * 28)
    # to a 4D tensor, compatible with our LeNetConvPoolLayer
    # (28, 28) is the size of MNIST images.
    layer0_input = x.reshape((batch_size, 3, 13, 13))

    
    net = twelve_net(layer0_input,batch_size)
    
    cost = net.log_regression_layer.negative_log_likelihood(y)
    
        # create a list of all model parameters to be fit by gradient descent
    params =  net.params

    # create a list of gradients for all model parameters
    grads = T.grad(cost, params)

    # train_model is a function that updates the model parameters by
    # SGD Since this model has many parameters, it would be tedious to
    # manually create an update rule for each model parameter. We thus
    # create the updates list by automatically looping over all
    # (params[i], grads[i]) pairs.
    updates = [
        (param_i, param_i - learning_rate * grad_i)
        for param_i, grad_i in zip(params, grads)
    ]

    
    train_model = theano.function(
        [index],
        cost,
        updates=updates,
        givens={
            x: train_set_x[index * batch_size: (index + 1) * batch_size],
            y: train_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )
    
    c = train_model(0);
    
    print "C : ",c
    print "THE END"
    
    
    

def get_test_data():
    img1 = imread('data/test/img_1.jpg')
    testimg1 = resize(img1,(13,13)).flatten()
    
    img2 = imread('data/test/img_47.jpg')
    testimg2 = resize(img2,(13,13)).flatten()
    t = testimg1[numpy.newaxis,...]
    
    list_imgs = numpy.concatenate([testimg1[numpy.newaxis,...],testimg2[numpy.newaxis,...]])
    
    #list_imgs = numpy.rollaxis(list_imgs,3,1)
    
    borrow = True
    shared_x = theano.shared(numpy.asarray(list_imgs,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
    shared_y = theano.shared(numpy.asarray( [1,0],
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
    
    return shared_x,T.cast(shared_y, 'int32')

def experiment():
    #collection = ImageCollection('data/test/*.jpg')

    evaluate_12net()
    
if __name__ == '__main__':
    experiment()



