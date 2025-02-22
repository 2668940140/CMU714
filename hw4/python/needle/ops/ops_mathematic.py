"""Operator implementations."""

from numbers import Number
from typing import Optional, List, Tuple, Union

from ..autograd import NDArray
from ..autograd import Op, Tensor, Value, TensorOp
from ..autograd import TensorTuple, TensorTupleOp
import numpy

# NOTE: we will import numpy as the array_api
# as the backend for our computations, this line will change in later homeworks

from ..backend_selection import array_api, BACKEND 
from .ops_tuple import *


class EWiseAdd(TensorOp):
    def compute(self, a: NDArray, b: NDArray):
        return a + b

    def gradient(self, out_grad: Tensor, node: Tensor):
        return out_grad, out_grad


def add(a, b):
    return EWiseAdd()(a, b)


class AddScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a: NDArray):
        return a + self.scalar

    def gradient(self, out_grad: Tensor, node: Tensor):
        return out_grad


def add_scalar(a, scalar):
    return AddScalar(scalar)(a)


class EWiseMul(TensorOp):
    def compute(self, a: NDArray, b: NDArray):
        return a * b

    def gradient(self, out_grad: Tensor, node: Tensor):
        lhs, rhs = node.inputs
        return out_grad * rhs, out_grad * lhs


def multiply(a, b):
    return EWiseMul()(a, b)


class MulScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a: NDArray):
        return a * self.scalar

    def gradient(self, out_grad: Tensor, node: Tensor):
        return (out_grad * self.scalar,)


def mul_scalar(a, scalar):
    return MulScalar(scalar)(a)


class PowerScalar(TensorOp):
    """Op raise a tensor to an (integer) power."""

    def __init__(self, scalar: int):
        self.scalar = scalar

    def compute(self, a: NDArray) -> NDArray:
        return a ** self.scalar

    def gradient(self, out_grad, node):
        return out_grad * self.scalar * (node.inputs[0] ** (self.scalar - 1))


def power_scalar(a, scalar):
    return PowerScalar(scalar)(a)


class EWisePow(TensorOp):
    """Op to element-wise raise a tensor to a power."""

    def compute(self, a: NDArray, b: NDArray) -> NDArray:
        return a**b

    def gradient(self, out_grad, node):
        if not isinstance(node.inputs[0], NDArray) or not isinstance(
            node.inputs[1], NDArray
        ):
            raise ValueError("Both inputs must be tensors (NDArray).")

        a, b = node.inputs[0], node.inputs[1]
        grad_a = out_grad * b * (a ** (b - 1))
        grad_b = out_grad * (a**b) * array_api.log(a.data)
        return grad_a, grad_b

def power(a, b):
    return EWisePow()(a, b)


class EWiseDiv(TensorOp):
    """Op to element-wise divide two nodes."""

    def compute(self, a, b):
        return a / b

    def gradient(self, out_grad, node):
        return out_grad / node.inputs[1], -out_grad * node.inputs[0] / (node.inputs[1] ** 2)


def divide(a, b):
    return EWiseDiv()(a, b)


class DivScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a):
        return a / self.scalar

    def gradient(self, out_grad, node):
        return out_grad / self.scalar


def divide_scalar(a, scalar):
    return DivScalar(scalar)(a)


class Transpose(TensorOp):
    def __init__(self, axes: Optional[tuple] = None):
        self.axes = axes

    def compute(self, a):
        if a.ndim <= 1:
            return a

        if self.axes is None:
            dim = a.ndim
            axes = (dim - 2, dim -1)
        else:
            axes = self.axes

        permute_order = list(range(a.ndim))
        permute_order[axes[0]] = axes[1]
        permute_order[axes[1]] = axes[0]
        return a.permute(permute_order)    



    def gradient(self, out_grad, node):
        return transpose(out_grad, axes=self.axes)


def transpose(a, axes=None):
    return Transpose(axes)(a)

class Permute(TensorOp):
    def __init__(self, axes: tuple):
        self.axes = axes

    def compute(self, a):
        return a.permute(self.axes)

    def gradient(self, out_grad, node):
        inverse_axes = [0] * len(self.axes)
        for i in range(len(self.axes)):
            inverse_axes[self.axes[i]] = i
        return permute(out_grad, inverse_axes)

def permute(a, axes):
    return Permute(axes)(a)

class Reshape(TensorOp):
    def __init__(self, shape):
        self.shape = shape

    def compute(self, a):
        return array_api.reshape(a, self.shape)

    def gradient(self, out_grad : Tensor, node):
        return reshape(out_grad, node.inputs[0].shape)

def reshape(a, shape):
    return Reshape(shape)(a)


class BroadcastTo(TensorOp):
    def __init__(self, shape):
        self.shape = shape

    def compute(self, a):
       return array_api.broadcast_to(a, self.shape)

    def gradient(self, out_grad, node):
        shape = node.inputs[0].shape
        extended = len(self.shape) - len(shape)
        ret = summation(out_grad, axes=tuple(range(extended)))
        axes = []
        for i in range(len(shape)):
            if shape[i] < ret.shape[i]:
                assert shape[i] == 1
                axes.append(i)
        ret = summation(ret, axes=tuple(axes))
        ret = reshape(ret, shape)
        return ret




def broadcast_to(a, shape):
    return BroadcastTo(shape)(a)


class Summation(TensorOp):
    def __init__(self, axes: Optional[tuple] = None):
        if isinstance(axes, int):
            self.axes = [axes]
        else:
            self.axes = axes


    def compute(self, a):
        out = array_api.sum(a, axis = self.axes)
        if self.axes is None:
            return out
        new_shape = []
        for i in range(len(a.shape)):
            if i not in self.axes:
                new_shape.append(a.shape[i])
        out = array_api.reshape(out, tuple(new_shape))
        return out

    def gradient(self, out_grad, node):
        oldshape = list(node.inputs[0].shape)
        newshape = oldshape.copy()
        if self.axes is None:
            axes = tuple(range(len(oldshape)))
        elif isinstance(self.axes, int):
            axes = [self.axes]
        else:
            axes = self.axes
        for axis in axes:
            newshape[axis] = 1
        ret = reshape(out_grad, newshape)
        return broadcast_to(ret, oldshape)
    


def summation(a, axes=None):
    return Summation(axes)(a)


class MatMul(TensorOp):
    def compute(self, a, b):
        return a @ b

    def gradient(self, out_grad, node):
        node0, node1 = node.inputs
        tr1 = transpose(node.inputs[1])
        tr0 = transpose(node.inputs[0])
        ret0 = matmul(out_grad, tr1)
        ret1 = matmul(tr0, out_grad)
        while ret0.shape.__len__() > node0.shape.__len__():
            ret0 = summation(ret0, axes=0)
        while ret1.shape.__len__() > node1.shape.__len__():
            ret1 = summation(ret1, axes=0)

        return ret0, ret1


def matmul(a, b):
    return MatMul()(a, b)


class Negate(TensorOp):
    def compute(self, a):
        return -a

    def gradient(self, out_grad, node):
        return negate(out_grad)


def negate(a):
    return Negate()(a)


class Log(TensorOp):
    def compute(self, a):
        return array_api.log(a)

    def gradient(self, out_grad, node):
        epsilon = 1e-8
        return out_grad / (node.inputs[0] + epsilon)


def log(a):
    return Log()(a)


class Exp(TensorOp):
    def compute(self, a):
        return array_api.exp(a)

    def gradient(self, out_grad, node):
        return out_grad * exp(node.inputs[0])


def exp(a):
    return Exp()(a)


class ReLU(TensorOp):
    def compute(self, a):
        return a * (a >= 0)

    def gradient(self, out_grad, node):

        cache_input = node.inputs[0].cached_data

        return out_grad * Tensor(array_api.greater_equal(cache_input, 0))


def relu(a):
    return ReLU()(a)

class Greater_or_equal(TensorOp):
    def compute(self, a):
        return array_api.greater_equal(a, 0)

    def gradient(self, out_grad, node):
        return out_grad * 0


class Tanh(TensorOp):
    def compute(self, a):
        return array_api.tanh(a)

    def gradient(self, out_grad, node):
        return out_grad * (1 - tanh(node.inputs[0]) ** 2)


def tanh(a):
    return Tanh()(a)

class Stack(TensorOp):
    def __init__(self, axis: int):
        """
        Concatenates a sequence of arrays along a new dimension.
        Parameters:
        axis - dimension to concatenate along
        All arrays need to be of the same size.
        """
        self.axis = axis

    def compute(self, args: TensorTuple) -> Tensor:
        shape = args[0].shape
        assert all(shape == arg.shape for arg in args)
        out = array_api.stack(args)
        permute_order = list(range(len(out.shape)))
        permute_order[self.axis] = 0
        for i in range(self.axis):
            permute_order[i] = i + 1
        out = out.permute(permute_order)
        return out

    def gradient(self, out_grad, node):
        return split(out_grad, self.axis)
        



def stack(args, axis):
    return Stack(axis)(make_tuple(*args))


class Split(TensorTupleOp):
    def __init__(self, axis: int):
        """
        Splits a tensor along an axis into a tuple of tensors.
        (The "inverse" of Stack)
        Parameters:
        axis - dimension to split
        """
        self.axis = axis

    def compute(self, A):
        permute_order = list(range(len(A.shape)))
        permute_order[0] = self.axis
        for i in range(1, self.axis + 1):
            permute_order[i] = i - 1
        A = A.permute(permute_order)
        out = array_api.split(A)
        return out

    def gradient(self, out_grad, node):
        return stack(out_grad, self.axis)


def split(a, axis):
    return Split(axis)(a)


class Flip(TensorOp):
    def __init__(self, axes: Optional[tuple] = None):
        self.axes = axes

    def compute(self, a):
        ### BEGIN YOUR SOLUTION
        out = a.compact()
        new_strides = list(out.strides)
        offset = 0
        if self.axes is None:
            for i in range(out.ndim):
                offset += (out.shape[i] - 1) * new_strides[i]
                new_strides[i] = -new_strides[i]
        else:
            for axis in self.axes:
                offset += (out.shape[axis] - 1) * new_strides[axis]
                new_strides[axis] = -new_strides[axis]

        out = NDArray.make(out.shape,
                                     strides=new_strides,
                                     device=out._device,
                                     handle=out._handle,
                                     offset=offset)
        out=out.compact()
        return out
    
        ### END YOUR SOLUTION

    def gradient(self, out_grad, node):
        return flip(out_grad, self.axes)


def flip(a, axes):
    return Flip(axes)(a)


class Dilate(TensorOp):
    def __init__(self, axes: tuple, dilation: int):
        if isinstance(axes, int):
            self.axes = (axes)
        else:
            self.axes = axes
        self.dilation = dilation

    def compute(self, a):
        ### BEGIN YOUR SOLUTION
        
        out = array_api.dilate(a, self.axes, self.dilation)
        return out

    def gradient(self, out_grad, node):
        ### BEGIN YOUR SOLUTION
        return undilate(out_grad, self.axes, self.dilation)
        ### END YOUR SOLUTION


def dilate(a, axes, dilation):
    return Dilate(axes, dilation)(a)


class UnDilate(TensorOp):
    def __init__(self, axes: tuple, dilation: int):
        if isinstance(axes, int):
            self.axes = (axes)
        else:
            self.axes = axes
        self.dilation = dilation

    def compute(self, a):
        ### BEGIN YOUR SOLUTION
        out = array_api.undilate(a, self.axes, self.dilation)
        return out
        ### END YOUR SOLUTION

    def gradient(self, out_grad, node):
        ### BEGIN YOUR SOLUTION
        return dilate(out_grad, self.axes, self.dilation)
        ### END YOUR SOLUTION


def undilate(a, axes, dilation):
    return UnDilate(axes, dilation)(a)


# NHWC format
class Conv(TensorOp):
    def __init__(self, stride: Optional[int] = 1, padding: Optional[int] = 0):
        self.stride = stride
        self.padding = padding

    def compute(self, A, B):
        if not self.padding is None:
            padding = [(0,0)]
            for i in range(2):
                padding.append((self.padding, self.padding))
            padding.append((0,0))
            A = array_api.pad(A, padding)

        # print(f"after pad A shape: {A.shape}, B shape: {B.shape}")
        N, H, W, C = A.shape
        KH, KW, CIN, COUT = B.shape
        assert KH == KW and CIN == C
        K = KH

        new_H = (H - K) // self.stride + 1
        new_W = (W - K) // self.stride + 1
        A = A.as_strided((N,new_H,new_W,K,K,C),
        (A.strides[0],A.strides[1] * self.stride,A.strides[2] * self.stride,
         A.strides[1],A.strides[2],A.strides[3]))
        A = A.compact()
        A = A.reshape((N*new_H*new_W,K*K*C))
        B = B.compact().reshape((K*K*C,COUT))
        out = A @ B
        out = out.reshape((N,new_H,new_W,COUT))
        return out

    def gradient(self, out_grad, node):
        out_grad = dilate(out_grad, (1,2), self.stride-1).detach()
        flipped_weight = flip(node.inputs[1], (0,1)).detach()
        flipped_weight = transpose(flipped_weight, (2,3)).detach()
        KH, KW, _, _ = node.inputs[1].shape
        assert KH == KW
        K = KH
        X_grad = conv(out_grad, flipped_weight,1,K-1-self.padding).detach()

        permute_X = permute(node.inputs[0], (3,1,2,0)).detach()
        permute_out_grad = permute(out_grad, (1, 2, 0, 3)).detach()

        W_grad = conv(permute_X, permute_out_grad,1,self.padding).detach()
        W_grad = permute(W_grad, (1, 2, 0, 3)).detach()

        assert W_grad.shape == node.inputs[1].shape and X_grad.shape == node.inputs[0].shape

        return X_grad, W_grad


def conv(a, b, stride=1, padding=1):
    return Conv(stride, padding)(a, b)
