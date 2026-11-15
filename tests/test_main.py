import os

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


def test_run_cleans_up_only_its_own_temp_file(gear):
    keep = gear.tmp / "output" / "keep.txt"  # e.g. files the engine/other steps left in ./output
    keep.parent.mkdir()
    keep.write_text("do not delete")

    run(gear.ctx)

    assert keep.exists()
    assert not os.path.exists(gear.acq.uploaded["path"])
