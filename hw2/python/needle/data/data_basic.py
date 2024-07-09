import numpy as np
from ..autograd import Tensor

from typing import Iterator, Optional, List, Sized, Union, Iterable, Any



class Dataset:
    r"""An abstract class representing a `Dataset`.

    All subclasses should overwrite :meth:`__getitem__`, supporting fetching a
    data sample for a given key. Subclasses must also overwrite
    :meth:`__len__`, which is expected to return the size of the dataset.
    """

    def __init__(self, transforms: Optional[List] = None):
        self.transforms = transforms

    def __getitem__(self, index) -> object:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
    
    def apply_transforms(self, x):
        if self.transforms is not None:
            # apply the transforms
            for tform in self.transforms:
                x = tform(x)
        return x


class DataLoader:
    r"""
    Data loader. Combines a dataset and a sampler, and provides an iterable over
    the given dataset.
    Args:
        dataset (Dataset): dataset from which to load the data.
        batch_size (int, optional): how many samples per batch to load
            (default: ``1``).
        shuffle (bool, optional): set to ``True`` to have the data reshuffled
            at every epoch (default: ``False``).
     """
    dataset: Dataset
    batch_size: Optional[int]

    def __init__(
        self,
        dataset: Dataset,
        batch_size: Optional[int] = 1,
        shuffle: bool = False,
    ):

        self.dataset = dataset
        self.shuffle = shuffle
        self.batch_size = batch_size
            
        self.has_y = dataset[0].__len__() == 2
        

    def __iter__(self):
        if not self.shuffle:
            self.ordering = np.array_split(np.arange(len(self.dataset)), 
            range(self.batch_size, len(self.dataset), self.batch_size))
        else:
            self.ordering = np.array_split(np.random.permutation(len(self.dataset)), 
            range(self.batch_size, len(self.dataset), self.batch_size))
        return self

    def __next__(self):
        if len(self.ordering) == 0:
            raise StopIteration
        indices = self.ordering.pop(0)
        batch = [self.dataset[i] for i in indices]

        x_batch =  np.array([item[0] for item in batch])
        if self.has_y:
            y_batch = np.array([item[1] for item in batch])
            return Tensor(x_batch),Tensor(y_batch)
        else:
            return (Tensor(x_batch),)
