import os
import sys
import pytest
from pathlib import Path
import bids
import json
from dmriprep.utils.bids import collect_data


@pytest.fixture
def input_dir_tree(tmp_path):
    data = {"002547": [1,2], "002548": [1], "002449": [1,2,3]}
    for sub, session in data.items():
        for ses in session:
            info = f"sub-{sub}/ses-{ses}"
            anat = os.path.join(tmp_path, info, "anat")
            dwi = os.path.join(tmp_path, info, "dwi")
            # make directories and files
            os.makedirs(anat)
            os.makedirs(dwi)
            tmpfilepath = os.path.join(anat, f"sub-{sub}_ses-{ses}_T1w.nii.gz")
            with open(tmpfilepath, "x") as f:
                f.write("placeholder text")
            tmpfilepath = os.path.join(dwi, f"sub-{sub}_ses-{ses}_dwi.bval")
            with open(tmpfilepath, "x") as f:
                f.write("placeholder text")
            tmpfilepath = os.path.join(dwi, f"sub-{sub}_ses-{ses}_dwi.bvec")
            with open(tmpfilepath, "x") as f:
                f.write("placeholder text")
            tmpfilepath = os.path.join(dwi, f"sub-{sub}_ses-{ses}_dwi.nii.gz")
            with open(tmpfilepath, "x") as f:
                f.write("placeholder text")
    #with open(os.path.join(tmp_path,"dataset_description.json"), "x") as f:
    #    f.write("placeholder text")

    name = Path(tmp_path).stem
    vers = bids.__version__
    out = dict(Name=name, BIDSVersion=vers)
    with open(os.path.join(tmp_path, "dataset_description.json"), "x") as f:
        f.write('{"BIDSVersion": "1.0.0", "License": "This dataset is made available under the Public Domain Dedication and License v1.0, whose full text can be found at www.opendatacommon We hope that all users will follow the ODC Attribution/Share-Aliommunityin particular, while not legally required, we hope that all users of the data will acknowledge the OpenfMRI project and NSF Grant OCI-1131441  Poldrack, PI in any publications.","Name": "Prefrontal-Subcortical Pathways Mediating Successful Emotion Regulation","ReferencesAndLinks": ["Wager, T.D., Davidson, M.L., Hughes, B.L., Lindquist, M.A., Ochsner, K.N. (2008). Prefrontal-subcortical pathways mediating successful emotion regulation. Neuron, 59(6):1037-50. doi: 10.1016/j.neuron.2008.09.006"]}')

    # Create non-BIDS files
    tmpfilepath = os.path.join(anat, f"dummy.txt")
    with open(tmpfilepath, "x") as f:
        f.write("placeholder text")
    tmpfilepath = os.path.join(dwi, f"sub-55.nii.gz")
    with open(tmpfilepath, "x") as f:
        f.write("placeholder text")

    return tmp_path, data


def test_collect_data(input_dir_tree):
    tmp_path, subjects = input_dir_tree
    subj_data, layout = collect_data(tmp_path, "sub-002548")