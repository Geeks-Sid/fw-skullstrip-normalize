# SDK gear to skull strip and normalize pre-processed imagess

This gear applies a brain mask and normalizes the skull-stripped image to the range 0-255.

Saves to a 'processed' acquisition in the same session as the input files.

## Usage

Run at the file-level.

### Inputs

* input-file: Image file to process (nifti)
* brain-mask: Binary brain mask

### Configuration

* __debug__ (boolean, default False): Include debug statements in output.

### Limitations
