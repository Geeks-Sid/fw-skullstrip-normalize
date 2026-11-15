import logging
import zipfile
import os
import tempfile

from flywheel_gear_toolkit import GearToolkitContext
from .run_level import get_analysis_run_level_and_hierarchy

from .im_functions import *
import nibabel as nib

log = logging.getLogger(__name__)


def output_filename(in_fn: str, tag: str = "_ss_norm") -> str:
    """Insert `tag` before the NIfTI extension; refuse anything that is not .nii/.nii.gz."""
    for ext in (".nii.gz", ".nii"):
        if in_fn.lower().endswith(ext):
            return in_fn[: -len(ext)] + tag + in_fn[-len(ext):]
    raise ValueError(f"Input must be a NIfTI file (.nii or .nii.gz), got: {in_fn}")

def run(gtk_context: GearToolkitContext):
    """Main entrypoint

    Args:
        gtk_context (GearToolkitContext)
    """
    fw = gtk_context.client

    # get the Flywheel hierarchy for the run
    destination_id = gtk_context.destination["id"]
    hierarchy = get_analysis_run_level_and_hierarchy(fw, destination_id)
    acq_label = hierarchy['acquisition_label']
    sub_label = hierarchy['subject_label']
    ses_label = hierarchy['session_label']
    project_label = hierarchy['project_label']
    group_name = hierarchy['group']

    # get the output acqusition container
    output_acq_label = 'processed'
    try:
        acq = fw.lookup(f'{group_name}/{project_label}/{sub_label}/{ses_label}/{output_acq_label}')
        acq = acq.reload()
    except:
        # if the acquisition does not exist, create it
        session = fw.lookup(f'{group_name}/{project_label}/{sub_label}/{ses_label}')
        acq = session.add_acquisition(label=output_acq_label)
        acq = acq.reload()
        log.info(f'Created new acquisition: {acq.id}')

    # get the input files
    im_file_path = gtk_context.get_input_path("input-file")
    mask_file_path = gtk_context.get_input_path("brain-mask")

    print(f'Processing file: {im_file_path}')
    img = nib.load(im_file_path)
    mask = nib.load(mask_file_path)

    new_img = normalize(skullstrip(img, mask))

    out_fn = output_filename(os.path.basename(im_file_path))

    # The SDK names the upload after the file on disk (upload_file has no `name` argument),
    # so write it under its final name in a private temp dir that is removed afterwards.
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, out_fn)
        nib.save(new_img, out_path)

        # upload to acquisition in the same session
        acq.upload_file(out_path)
