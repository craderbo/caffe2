## @package normalization
# Module caffe2.python.helpers.normalization
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from caffe2.python import core


def lrn(model, blob_in, blob_out, **kwargs):
    """LRN"""
    return model.net.LRN(
        blob_in,
        [blob_out, "_" + blob_out + "_scale"],
        order=model.order,
        **kwargs
    )[0]


def softmax(model, blob_in, blob_out=None, use_cudnn=False, **kwargs):
    """Softmax."""
    if use_cudnn:
        kwargs['engine'] = 'CUDNN'
    if blob_out is not None:
        return model.net.Softmax(blob_in, blob_out, **kwargs)
    else:
        return model.net.Softmax(blob_in, **kwargs)


def instance_norm(model, blob_in, blob_out, dim_in, order="NCHW", **kwargs):
    blob_out = blob_out or model.net.NextName()
    # Input: input, scale, bias
    # Output: output, saved_mean, saved_inv_std
    # scale: initialize with ones
    # bias: initialize with zeros

    def init_blob(value, suffix):
        return model.param_init_net.ConstantFill(
            [], blob_out + "_" + suffix, shape=[dim_in], value=value)
    scale, bias = init_blob(1.0, "s"), init_blob(0.0, "b")

    model.params.extend([scale, bias])
    model.weights.append(scale)
    model.biases.append(bias)
    blob_outs = [blob_out, blob_out + "_sm", blob_out + "_siv"]
    if 'is_test' in kwargs and kwargs['is_test']:
        blob_outputs = model.net.InstanceNorm(
            [blob_in, scale, bias], [blob_out],
            order=order, **kwargs)
        return blob_outputs
    else:
        blob_outputs = model.net.InstanceNorm(
            [blob_in, scale, bias], blob_outs,
            order=order, **kwargs)
        # Return the output
        return blob_outputs[0]


def spatial_bn(model, blob_in, blob_out, dim_in, order="NCHW", **kwargs):
    blob_out = blob_out or model.net.NextName()
    # Input: input, scale, bias, est_mean, est_inv_var
    # Output: output, running_mean, running_inv_var, saved_mean,
    #         saved_inv_var
    # scale: initialize with ones
    # bias: initialize with zeros
    # est mean: zero
    # est var: ones

    def init_blob(value, suffix):
        return model.param_init_net.ConstantFill(
            [], blob_out + "_" + suffix, shape=[dim_in], value=value)

    if model.init_params:
        scale, bias = init_blob(1.0, "s"), init_blob(0.0, "b")
        running_mean = init_blob(0.0, "rm")
        running_inv_var = init_blob(1.0, "riv")
    else:
        scale = core.ScopedBlobReference(
            blob_out + '_s', model.param_init_net)
        bias = core.ScopedBlobReference(
            blob_out + '_b', model.param_init_net)
        running_mean = core.ScopedBlobReference(
            blob_out + '_rm', model.param_init_net)
        running_inv_var = core.ScopedBlobReference(
            blob_out + '_riv', model.param_init_net)

    model.params.extend([scale, bias])
    model.computed_params.extend([running_mean, running_inv_var])
    model.weights.append(scale)
    model.biases.append(bias)
    blob_outs = [blob_out, running_mean, running_inv_var,
                 blob_out + "_sm", blob_out + "_siv"]
    if 'is_test' in kwargs and kwargs['is_test']:
        blob_outputs = model.net.SpatialBN(
            [blob_in, scale, bias, blob_outs[1], blob_outs[2]], [blob_out],
            order=order, **kwargs)
        return blob_outputs
    else:
        blob_outputs = model.net.SpatialBN(
            [blob_in, scale, bias, blob_outs[1], blob_outs[2]], blob_outs,
            order=order, **kwargs)
        # Return the output
        return blob_outputs[0]
