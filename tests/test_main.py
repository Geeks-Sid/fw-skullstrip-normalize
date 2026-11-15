import numpy as np

from fw_skullstrip_normalize.main import run


def test_run_masks_then_normalizes_and_uploads(gear):
    run(gear.ctx)

    gear.acq.upload_file.assert_called_once()
    assert gear.acq.uploaded["name"] == "sub-01_T1w_ss_norm.nii.gz"

    out = gear.acq.uploaded["data"]
    brain = (slice(2, 6),) * 3
    outside = np.ones(out.shape, dtype=bool)
    outside[brain] = False
    assert not out[outside].any()  # skull removed
    # normalization ranges over the brain only: skull (1000) must not squash it
    assert out[brain].max() == 255
