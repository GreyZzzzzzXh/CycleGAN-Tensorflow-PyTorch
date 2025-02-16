from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial

import tensorflow as tf
import tensorflow.contrib.slim as slim


conv = partial(slim.conv2d, activation_fn=None)
deconv = partial(slim.conv2d_transpose, activation_fn=None)
relu = tf.nn.relu
lrelu = partial(tf.nn.leaky_relu, alpha=0.2)


def bn(inputs):
    with tf.variable_scope("BatchNorm"):
        inputs = tf.identity(inputs)
        channels = inputs.get_shape()[3]
        offset = tf.get_variable("offset", [channels], dtype=tf.float32, initializer=tf.zeros_initializer())
        scale = tf.get_variable("scale", [channels], dtype=tf.float32, initializer=tf.random_normal_initializer(1.0, 0.02))
        mean, variance = tf.nn.moments(inputs, axes=[0, 1, 2], keep_dims=False)
        variance_epsilon = 1e-5
        normalized = tf.nn.batch_normalization(inputs, mean, variance, offset, scale, variance_epsilon=variance_epsilon)

        return normalized


def discriminator(img, scope, dim=64):
    conv_bn_lrelu = partial(conv, normalizer_fn=bn, activation_fn=lrelu, biases_initializer=None)

    with tf.variable_scope(scope + '_discriminator', reuse=tf.AUTO_REUSE):
        net = lrelu(conv(img, dim, 4, 2))
        net = conv_bn_lrelu(net, dim * 2, 4, 2)
        net = conv_bn_lrelu(net, dim * 4, 4, 2)
        net = conv_bn_lrelu(net, dim * 8, 4, 1)
        net = conv(net, 1, 4, 1)

        return net


def generator(img, scope, dim=64):
    conv_bn_relu = partial(conv, normalizer_fn=bn, activation_fn=relu, biases_initializer=None)
    deconv_bn_relu = partial(deconv, normalizer_fn=bn, activation_fn=relu, biases_initializer=None)

    def _residule_block(x, dim):
        y = conv_bn_relu(x, dim, 3, 1)
        y = bn(conv(y, dim, 3, 1))
        return y + x

    with tf.variable_scope(scope + '_generator', reuse=tf.AUTO_REUSE):
        net = conv_bn_relu(img, dim, 7, 1)
        net = conv_bn_relu(net, dim * 2, 3, 2)
        net = conv_bn_relu(net, dim * 4, 3, 2)

        for i in range(9):
            net = _residule_block(net, dim * 4)

        net = deconv_bn_relu(net, dim * 2, 3, 2)
        net = deconv_bn_relu(net, dim, 3, 2)
        net = conv(net, 3, 7, 1)
        net = tf.nn.tanh(net)

        return net
