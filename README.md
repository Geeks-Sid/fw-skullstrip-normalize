# SDK gear to skull strip and normalize pre-processed images

This gear applies a brain mask and then normalizes the skull-stripped image to the range 0-255.

Normalization clips intensities at the 99.99th percentile, then scales linearly from the image minimum to that percentile. The result is stored as int16.

Saves to a 'processed' acquisition in the same session as the input files (created if missing).

## Usage

Run at the file-level, on a file in an acquisition.

### Inputs

* input-file: Image file to process (nifti, `.nii` or `.nii.gz`)
* brain-mask: Brain mask (nifti). Any non-zero voxel is treated as brain. Must have the same shape and affine as the input image.

### Configuration

* __debug__ (boolean, default False): Include debug statements in output.

### Outputs

`<input name>_ss_norm.nii[.gz]` in the session's 'processed' acquisition, with the source file name, mask name and gear version recorded under the file's `info.skullstrip_normalize`. An existing file with the same name is replaced (a warning is logged).

### Limitations

* 3D images only; a 4D image or a mask of a different shape fails.
* The gear fails, rather than writing an image, if the masked image is constant or empty (e.g. an empty mask) or contains NaN inside the mask.

## Development

```
pip install -r requirements-dev.txt
pytest
```

Tests use synthetic images and a faked Flywheel client; they do not contact Flywheel.
