import nibabel as nib
import numpy as np

def normalize(img):
    # Normalize the image to the range 0-255

    img_data = img.get_fdata()
    img_data = np.float32(img_data)

    MP_RC = np.percentile(img_data, 99.99)  # Find the 99.99th percentile
    # min_val = np.percentile(img_data, 1)
    min_val = np.percentile(img_data,0)
    # print(min_val)
    # min_val = img_data.min()
    # img_data[img_data <= min_val] = min_val

    # constant data (e.g. an empty mask) divides by zero, and NaN/inf poisons the percentiles;
    # both cast to garbage int16 silently, so fail instead of writing a bad image
    if not (np.isfinite(MP_RC) and np.isfinite(min_val)) or MP_RC <= min_val:
        raise ValueError("Cannot normalize: image is constant or empty (empty brain mask?) or has NaN/inf values.")
    img_data[img_data > MP_RC] = MP_RC

    img_data = ((img_data - min_val) * 255.0) / (MP_RC - min_val)
    img_data = np.rint(img_data).astype('int16')

    normalized_image = nib.Nifti1Image(img_data, img.affine, img.header)

    return normalized_image

def skullstrip(img, mask):
    # a broadcastable-but-wrong mask, or one on a different grid, would silently corrupt the output
    if img.shape != mask.shape:
        raise ValueError(f"Mask shape {mask.shape} does not match image shape {img.shape}.")
    if not np.allclose(img.affine, mask.affine, atol=1e-3):
        raise ValueError("Mask and image affines differ: the mask is not in the image's space.")

    img_data = img.get_fdata()
    # img_data = np.float32(img_data)
    mask_data = mask.get_fdata()

    # apply brain mask: any non-zero voxel is brain. np.where, not multiplication, so a
    # non-binary mask cannot rescale intensities and NaN/inf outside the mask cannot leak in
    ss_img_data = np.where(mask_data != 0, img_data, 0)

    # img_data = np.rint(ss_img_data).astype('int16')

    ss_img = nib.Nifti1Image(ss_img_data, img.affine, img.header)

    return ss_img

