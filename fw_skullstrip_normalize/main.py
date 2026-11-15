import logging
import zipfile
import os
import shutil
import json

from flywheel_gear_toolkit import GearToolkitContext
from .run_level import get_analysis_run_level_and_hierarchy

from .im_functions import *
import nibabel as nib

log = logging.getLogger(__name__)

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

    # get the input file
    CONFIG_FILE_PATH = '/flywheel/v0/config.json'
    with open(CONFIG_FILE_PATH) as config_file:
        config = json.load(config_file)

    im_file_path = config['inputs']['input-file']['location']['path'] # input path in the gear container
    mask_file_path = config['inputs']['brain-mask']['location']['path'] # input path in the gear container

    print(f'Processing file: {im_file_path}')
    img = nib.load(im_file_path)
    mask = nib.load(mask_file_path)

    normed_img = zscore_normalize(img)
    new_img = skullstrip(normed_img, mask)

    in_fn = os.path.basename(im_file_path) # get just the base file name
    if 'gz' in in_fn.split('.nii')[-1]:
        file_ending = '.nii.gz'
    else:
        file_ending = '.nii'
    out_fn = in_fn.split('.nii')[0] + '_ss_norm' + file_ending  # append _ss to the original file name
    out_path = f'output/{out_fn}'

    nib.save(new_img, out_path)

    # upload to acquisition in the same session
    acq.upload_file(out_path, name=out_fn)

    # remove temp files
    shutil.rmtree('output', ignore_errors=True)
