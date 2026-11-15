"""Fixtures that fake the Flywheel API and gear context; nothing here talks to a server."""
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import nibabel as nib
import numpy as np
import pytest

IN_NAME = "sub-01_T1w.nii.gz"


def make_images(tmp_path, in_name=IN_NAME):
    """Write a 3D image with a bright 'skull' shell around a dim 'brain', plus its mask."""
    data = np.full((8, 8, 8), 1000.0, dtype=np.float32)  # skull / head
    brain = (slice(2, 6),) * 3
    data[brain] = np.arange(1, 65, dtype=np.float32).reshape(4, 4, 4)
    mask = np.zeros((8, 8, 8), dtype=np.uint8)
    mask[brain] = 1

    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    in_path = tmp_path / in_name
    mask_path = tmp_path / "mask.nii.gz"
    nib.save(nib.Nifti1Image(data, affine), str(in_path))
    nib.save(nib.Nifti1Image(mask, affine), str(mask_path))
    return in_path, mask_path


@pytest.fixture
def gear(tmp_path, monkeypatch):
    """A fake GearToolkitContext for an acquisition-level run, plus the 'processed' acquisition mock."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    in_path, mask_path = make_images(tmp_path)

    parents = {"group": "grp", "project": "proj", "subject": "sub", "session": "ses"}
    containers = {
        "dest": SimpleNamespace(
            container_type="acquisition", label="acq", parents={**parents, "acquisition": "dest"}
        ),
        "proj": SimpleNamespace(label="Project"),
        "sub": SimpleNamespace(label="Subject"),
        "ses": SimpleNamespace(label="Session"),
    }

    acq = MagicMock(name="processed_acquisition")
    acq.reload.return_value = acq
    # capture what would be uploaded: the file is temporary
    acq.uploaded = {}

    def capture(path, **kwargs):
        acq.uploaded["name"] = os.path.basename(path)
        acq.uploaded["data"] = np.asarray(nib.load(path).dataobj)

    acq.upload_file.side_effect = capture

    client = MagicMock(name="client")
    client.get.side_effect = containers.__getitem__
    client.lookup.return_value = acq

    ctx = MagicMock(name="gear_context")
    ctx.client = client
    ctx.destination = {"id": "dest"}
    ctx.get_input_path.side_effect = {"input-file": str(in_path), "brain-mask": str(mask_path)}.__getitem__
    return SimpleNamespace(ctx=ctx, client=client, acq=acq, in_path=in_path, mask_path=mask_path, tmp=tmp_path)
