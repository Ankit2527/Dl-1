################################################################################
# MIT License
#
# Copyright (c) 2021
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to conditions.
#
# Author: Deep Learning Course | Fall 2021
# Date Created: 2020-11-27
################################################################################

import torch
from torchvision.utils import make_grid
import numpy as np


def sample_reparameterize(mean, std):
    """
    Perform the reparameterization trick to sample from a distribution with the given mean and std
    Inputs:
        mean - Tensor of arbitrary shape and range, denoting the mean of the distributions
        std - Tensor of arbitrary shape with strictly positive values. Denotes the standard deviation
              of the distribution
    Outputs:
        z - A sample of the distributions, with gradient support for both mean and std.
            The tensor should have the same shape as the mean and std input tensors.
    """
    assert not (std < 0).any().item(), "The reparameterization trick got a negative std as input. " + \
                                       "Are you sure your input is std and not log_std?"
                                       
    eps = torch.randn_like(std)
    z = mean + std * eps

    return z


def KLD(mean, log_std):
    """
    Calculates the Kullback-Leibler divergence of given distributions to unit Gaussians over the last dimension.
    See Section 1.3 for the formula.
    Inputs:
        mean - Tensor of arbitrary shape and range, denoting the mean of the distributions.
        log_std - Tensor of arbitrary shape and range, denoting the log standard deviation of the distributions.
    Outputs:
        KLD - Tensor with one less dimension than mean and log_std (summed over last dimension).
              The values represent the Kullback-Leibler divergence to unit Gaussians.
    """

    log_var = 2 * log_std
    KLD = - 0.5 * torch.sum(1 - torch.exp(log_var) - mean.pow(2) + log_var, dim = 1)
    return KLD


def elbo_to_bpd(elbo, img_shape):
    """
    Converts the summed negative log likelihood given by the ELBO into the bits per dimension score.
    Inputs:
        elbo - Tensor of shape [batch_size]
        img_shape - Shape of the input images, representing [batch, channels, height, width]
    Outputs:
        bpd - The negative log likelihood in bits per dimension for the given image.
    """
    ch = torch.log2(torch.exp(torch.tensor([1.0]))) \
        / torch.prod(torch.tensor(img_shape[1:]))
    ch = ch.item()
    
    bpd = elbo * ch
    return bpd


@torch.no_grad()
def visualize_manifold(decoder, grid_size=20):
    """
    Visualize a manifold over a 2 dimensional latent space. The images in the manifold
    should represent the decoder's output means (not binarized samples of those).
    Inputs:
        decoder - Decoder model such as LinearDecoder or ConvolutionalDecoder.
        grid_size - Number of steps/images to have per axis in the manifold.
                    Overall you need to generate grid_size**2 images, and the distance
                    between different latents in percentiles is 1/grid_size
    Outputs:
        img_grid - Grid of images representing the manifold.
    """

    ## Hints:
    # - You can use the icdf method of the torch normal distribution  to obtain z values at percentiles.
    # - Use the range [0.5/grid_size, 1.5/grid_size, ..., (grid_size-0.5)/grid_size] for the percentiles.
    # - torch.meshgrid might be helpful for creating the grid of values
    # - You can use torchvision's function "make_grid" to combine the grid_size**2 images into a grid
    # - Remember to apply a sigmoid after the decoder

    # Compute the desired quantiles
    percentiles = np.arange(0.5/(grid_size+1), (grid_size+0.5)/(grid_size+1), 1.0/(grid_size+1))
    percentiles = torch.from_numpy(percentiles)
    normal = torch.distributions.Normal(0,1)
    z = normal.icdf(percentiles)
    z1, z2 = torch.meshgrid(z, z)
    z = torch.stack([z1.reshape(-1), z2.reshape(-1)], dim=1).float()
    output = decoder(z)
    output = torch.softmax(output, dim =1)
    batch_size, _, _, _ = output.size()
    output = torch.permute(output,(0,2,3,1))
    output = torch.flatten(output, 0,2)
    x_samples = torch.multinomial(output, num_samples=1)
    x_samples = x_samples.reshape(batch_size,1,28,28)
    x_samples = x_samples / 15
    img_grid = make_grid(x_samples, nrow=grid_size, value_range=(0, 1))
    return img_grid
