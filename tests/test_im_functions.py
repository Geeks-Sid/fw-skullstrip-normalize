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


@pytest.mark.parametrize("mask_shape", [(2, 2, 1), (2, 2, 3), (2, 2)])  # (2,2,1) broadcasts; must still fail
def test_skullstrip_rejects_mask_with_different_shape(mask_shape):
    with pytest.raises(ValueError, match="shape"):
        skullstrip(nii(np.ones((2, 2, 2))), nii(np.ones(mask_shape)))


def test_skullstrip_rejects_mask_in_a_different_space_but_tolerates_float_noise():
    img = nii(np.ones((2, 2, 2)))
    shifted = np.eye(4)
    shifted[0, 3] = 5.0  # 5 mm translation: same grid size, different place
    with pytest.raises(ValueError, match="affine"):
        skullstrip(img, nii(np.ones((2, 2, 2)), shifted))

    noisy = np.eye(4) + 1e-7
    skullstrip(img, nii(np.ones((2, 2, 2)), noisy))  # must not raise


def test_normalize_scales_to_0_255_and_clips_at_99_99th_percentile():
    # >10k voxels so a single outlier lies above the 99.99th percentile
    data = np.arange(22**3, dtype=np.float32).reshape(22, 22, 22)
    data.flat[0] = 1e6  # clipped to the percentile instead of squashing the rest into 0-1

    out = normalize(nii(data)).get_fdata()

    assert out.min() == 0
    assert out.max() == 255
    assert 238 <= out.flat[10000] <= 241  # (10000 - min) / (p99.99 - min) * 255, unaffected by the outlier


@pytest.mark.parametrize(
    "bad",
    [np.zeros((2, 2, 2)), np.full((2, 2, 2), 7.0), np.array([[[np.nan, 1], [2, 3]], [[4, 5], [6, 7]]])],
    ids=["all-zero (empty mask)", "constant", "nan"],
)
def test_normalize_refuses_data_it_cannot_scale(bad):
    with pytest.raises(ValueError, match="Cannot normalize"):
        normalize(nii(bad))
