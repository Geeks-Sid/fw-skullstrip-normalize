from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from fw_skullstrip_normalize.run_level import get_analysis_run_level_and_hierarchy


def fake_client(destination, **labels):
    containers = {"dest": destination, **{k: SimpleNamespace(label=v) for k, v in labels.items()}}
    client = MagicMock()
    client.get.side_effect = containers.__getitem__
    return client


def test_acquisition_destination_returns_group_id_and_labels():
    parents = {"group": "grp", "project": "p", "subject": "s", "session": "ses"}
    dest = SimpleNamespace(container_type="acquisition", label="T1w", parents=parents)
    client = fake_client(dest, p="Proj", s="Subj", ses="Sess")

    assert get_analysis_run_level_and_hierarchy(client, "dest") == {
        "group": "grp",
        "project_label": "Proj",
        "subject_label": "Subj",
        "session_label": "Sess",
        "acquisition_label": "T1w",
    }


@pytest.mark.parametrize("container_type", ["session", "analysis", "project"])
def test_non_acquisition_destination_is_rejected(container_type):
    dest = SimpleNamespace(container_type=container_type, label="x", parents={})

    with pytest.raises(ValueError, match="acquisition"):
        get_analysis_run_level_and_hierarchy(fake_client(dest), "dest")
