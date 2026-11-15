import logging
import os
import tempfile

import nibabel as nib
from flywheel import ApiException
from flywheel_gear_toolkit import GearToolkitContext

from . import __version__
from .im_functions import normalize, skullstrip
from .run_level import get_analysis_run_level_and_hierarchy

log = logging.getLogger(__name__)


def output_filename(in_fn: str, tag: str = "_ss_norm") -> str:
    """Insert `tag` before the NIfTI extension; refuse anything that is not .nii/.nii.gz."""
    for ext in (".nii.gz", ".nii"):
        if in_fn.lower().endswith(ext):
            return in_fn[: -len(ext)] + tag + in_fn[-len(ext):]
    raise ValueError(f"Input must be a NIfTI file (.nii or .nii.gz), got: {in_fn}")


def get_or_create_output_acquisition(fw, session_path: list, label: str):
    """Return the session's `label` acquisition, creating it only if the lookup says it is missing."""
    try:
        # a list path (not 'a/b/c') keeps labels containing '/' intact
        return fw.lookup(session_path + [label]).reload()
    except ApiException as exc:
        if exc.status != 404:  # permissions/network/server errors must not create a duplicate
            raise
    acq = fw.lookup(session_path).add_acquisition(label=label).reload()
    log.info(f"Created new acquisition: {acq.id}")
    return acq

def run(gtk_context: GearToolkitContext):
    """Main entrypoint

    Args:
        gtk_context (GearToolkitContext)
    """
    fw = gtk_context.client

    # get the input files
    im_file_path = gtk_context.get_input_path("input-file")
    mask_file_path = gtk_context.get_input_path("brain-mask")
    out_fn = output_filename(os.path.basename(im_file_path))

    # Process before touching Flywheel: a bad input must not leave an empty 'processed' acquisition.
    log.info(f"Processing file: {im_file_path}")
    img = nib.load(im_file_path)
    mask = nib.load(mask_file_path)
    new_img = normalize(skullstrip(img, mask))

    # get the Flywheel hierarchy for the run
    destination_id = gtk_context.destination["id"]
    hierarchy = get_analysis_run_level_and_hierarchy(fw, destination_id)
    session_path = [
        hierarchy["group"],
        hierarchy["project_label"],
        hierarchy["subject_label"],
        hierarchy["session_label"],
    ]
    acq = get_or_create_output_acquisition(fw, session_path, "processed")

    if acq.get_file(out_fn):  # uploading the same name replaces the file; make that visible
        log.warning(f"'{out_fn}' already exists in acquisition {acq.id} and will be replaced.")

    # The SDK names the upload after the file on disk (upload_file has no `name` argument),
    # so write it under its final name in a private temp dir that is removed afterwards.
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, out_fn)
        nib.save(new_img, out_path)

        # upload to acquisition in the same session
        acq.upload_file(out_path)

    # provenance: record what produced the file so outputs can be audited later
    acq.update_file_info(
        out_fn,
        {
            "skullstrip_normalize": {
                "source_file": os.path.basename(im_file_path),
                "brain_mask": os.path.basename(mask_file_path),
                "gear_version": __version__,
            }
        },
    )
