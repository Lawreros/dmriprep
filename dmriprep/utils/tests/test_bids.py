import os
import sys
import pytest
from pathlib import Path
import bids
import json
from dmriprep.utils.bids import collect_data, write_derivative_description, validate_input_dir





def test_collect_data(dipy_test_data):
    # Only asserts that collect_data runs, need to actually check the structure of the variable
    bvals = dipy_test_data['bvals']
    _dipy_datadir_root = os.getenv('DMRIPREP_TESTS_DATA') or Path.home()
    dipy_datadir = Path(_dipy_datadir_root) / '.cache' / 'data'
    #dipy_datadir.mkdir(parents=True, exist_ok=True)
    #tmp_path, subjects = input_dir_tree

    name = Path(dipy_datadir).stem
    vers = bids.__version__
    out = dict(Name=name, BIDSVersion=vers)
    with open(os.path.join(dipy_datadir, "dataset_description.json"), "w") as f:
        f.write('{"BIDSVersion": "1.0.0", "License": "This dataset is made available under the Public Domain Dedication and License v1.0, whose full text can be found at www.opendatacommon We hope that all users will follow the ODC Attribution/Share-Aliommunityin particular, while not legally required, we hope that all users of the data will acknowledge the OpenfMRI project and NSF Grant OCI-1131441  Poldrack, PI in any publications.","Name": "Prefrontal-Subcortical Pathways Mediating Successful Emotion Regulation","ReferencesAndLinks": ["Wager, T.D., Davidson, M.L., Hughes, B.L., Lindquist, M.A., Ochsner, K.N. (2008). Prefrontal-subcortical pathways mediating successful emotion regulation. Neuron, 59(6):1037-50. doi: 10.1016/j.neuron.2008.09.006"]}')

    subj_data, layout = collect_data(dipy_datadir, "data")
    assert subj_data
    assert layout

def test_write_derivative_description(input_dir_tree):
    tmp_path, subjects = input_dir_tree
    write_derivative_description(tmp_path, tmp_path)
    desc_file=tmp_path / 'dataset_description.json'
    assert desc_file.exists()

def test_validate_input_dir(input_dir_tree):
    tmp_path, subjects = input_dir_tree
    exec_env = os.name

    # special variable set in the container
    if os.getenv('IS_DOCKER_8395080871'):
        exec_env = 'singularity'
        cgroup = Path('/proc/1/cgroup')
        if cgroup.exists() and 'docker' in cgroup.read_text():
            exec_env = 'docker'
            if os.getenv('DOCKER_VERSION_8395080871'):
                exec_env = 'dmriprep-docker'

    validate_input_dir(exec_env, tmp_path, None) #Need to figure out issue with subject not being found
