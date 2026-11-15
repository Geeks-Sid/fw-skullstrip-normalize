import os
from unittest.mock import MagicMock

import numpy as np
import pytest
from flywheel import ApiException

from fw_skullstrip_normalize.main import output_filename, run


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


@pytest.mark.parametrize(
    "in_fn, expected",
    [
        ("sub-01_T1w.nii.gz", "sub-01_T1w_ss_norm.nii.gz"),
        ("sub-01_T1w.nii", "sub-01_T1w_ss_norm.nii"),
        ("SUB.NII.GZ", "SUB_ss_norm.NII.GZ"),
        # '.nii' inside the name used to truncate it (-> 'sub_ss_norm.nii.gz'), colliding across files
        ("sub.niilab_T1w.nii.gz", "sub.niilab_T1w_ss_norm.nii.gz"),
    ],
)
def test_output_filename(in_fn, expected):
    assert output_filename(in_fn) == expected


@pytest.mark.parametrize("in_fn", ["scan.mgz", "scan.nii.gz.bak", "scan"])
def test_output_filename_rejects_non_nifti(in_fn):
    with pytest.raises(ValueError, match="NIfTI"):
        output_filename(in_fn)


def not_found(path):
    raise ApiException(status=404, reason="Not Found")


def test_run_uses_existing_processed_acquisition(gear):
    run(gear.ctx)

    # list path: labels may contain '/', which a 'a/b/c' string would split apart
    gear.client.lookup.assert_called_once_with(["grp", "Project", "Subject", "Session", "processed"])
    gear.acq.upload_file.assert_called_once()


def test_run_creates_processed_acquisition_only_on_404(gear):
    session = MagicMock(name="session")
    session.add_acquisition.return_value = gear.acq
    gear.client.lookup.side_effect = lambda path: not_found(path) if len(path) == 5 else session

    run(gear.ctx)

    session.add_acquisition.assert_called_once_with(label="processed")
    gear.acq.upload_file.assert_called_once()


def test_run_does_not_create_acquisition_on_other_api_errors(gear):
    gear.client.lookup.side_effect = ApiException(status=500, reason="Server Error")

    with pytest.raises(ApiException):
        run(gear.ctx)

    gear.client.lookup.assert_called_once()  # no fallback lookup of the session to create into
    gear.acq.upload_file.assert_not_called()
