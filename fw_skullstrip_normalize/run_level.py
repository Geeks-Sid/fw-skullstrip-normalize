# based on https://github.com/flywheel-apps/bids-fmriprep/blob/main/utils/bids/run_level.py

#!/usr/bin/env python3
"""Determine level at which the gear is running."""

import logging

log = logging.getLogger(__name__)


def get_analysis_run_level_and_hierarchy(gtk_context_client, destination_id):
    """Determine the level at which a job is running, given a destination
    Args:
        gtk_context_client (gear_toolkit.GearToolkitContext.client): flywheel client
        destination_id (id): id of the destination of the gear
    Returns:
        hierarchy (dict): containing the run_level and labels for the
            run_label, group, project, subject, session, and
            acquisition.
    """

    hierarchy = {
        "group": None,
        "project_label": None,
        "subject_label": None,
        "session_label": None,
        "acquisition_label":None
    }

    run_level = 'acquisition'
    destination = gtk_context_client.get(destination_id)

    if destination.container_type != run_level:
        # returning an all-None hierarchy only surfaces later as a lookup of 'None/None/...'
        raise ValueError(
            f"The gear destination must be an {run_level}, got {destination.container_type!r}."
        )

    hierarchy["group"] = destination.parents["group"]

    for level in ["project", "subject", "session", "acquisition"]:
        if level == run_level:
            hierarchy[f"{level}_label"] = destination.label
        elif destination.parents[level]:
            container = gtk_context_client.get(destination.parents[level])
            hierarchy[f"{level}_label"] = container.label

    log.info(f"Gear run level and hierarchy labels: {hierarchy}")
    return hierarchy
