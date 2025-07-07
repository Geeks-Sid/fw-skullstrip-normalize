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

    img_data[img_data > MP_RC] = MP_RC

    img_data = ((img_data - min_val) * 255.0) / (MP_RC - min_val)
    img_data = np.rint(img_data).astype('int16')

    normalized_image = nib.Nifti1Image(img_data, img.affine, img.header)

    return normalized_image

def skullstrip(img, mask):

    img_data = img.get_fdata()
    # img_data = np.float32(img_data)
    mask_data = mask.get_fdata()

    # apply brain mask
    ss_img_data = img_data * mask_data

    # img_data = np.rint(ss_img_data).astype('int16')

    ss_img = nib.Nifti1Image(ss_img_data, img.affine, img.header)

    return ss_img

