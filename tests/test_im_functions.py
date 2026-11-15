import nibabel as nib
import numpy as np
import pytest

from fw_skullstrip_normalize.im_functions import normalize, skullstrip


def nii(data, affine=None):
    return nib.Nifti1Image(np.asarray(data), np.eye(4) if affine is None else affine)


def test_skullstrip_treats_any_nonzero_mask_voxel_as_brain():
    img = nii(np.full((2, 2, 2), 10.0))
    mask = nii(np.array([[[0, 1], [3, 0]], [[0, 0], [0, 0.5]]]))  # label-style / soft mask values

    out = skullstrip(img, mask).get_fdata()

    assert set(np.unique(out)) == {0.0, 10.0}  # used to be scaled by 3 and 0.5
    assert out.sum() == 30.0


def test_skullstrip_does_not_leak_nan_or_inf_from_outside_the_mask():
    data = np.ones((2, 2, 2))
    data[0, 0, 0] = np.nan
    data[1, 1, 1] = np.inf
    mask = np.ones((2, 2, 2))
    mask[0, 0, 0] = mask[1, 1, 1] = 0

    out = skullstrip(nii(data), nii(mask)).get_fdata()

    assert np.isfinite(out).all()  # NaN * 0 is NaN
