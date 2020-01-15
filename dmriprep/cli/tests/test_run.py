"""Test CLI."""
from packaging.version import Version
import pytest
from .. import version as _version
from ... import __about__
from ..run import get_parser, check_deps


@pytest.mark.parametrize(('current', 'latest'), [
    ('1.0.0', '1.3.2'),
    ('1.3.2', '1.3.2')
])
def test_get_parser_update(monkeypatch, capsys, current, latest):
    """Make sure the out-of-date banner is shown."""
    expectation = Version(current) < Version(latest)

    def _mock_check_latest(*args, **kwargs):
        return Version(latest)

    monkeypatch.setattr(__about__, '__version__', current)
    monkeypatch.setattr(_version, 'check_latest', _mock_check_latest)

    get_parser()
    captured = capsys.readouterr().err

    msg = """\
You are using dMRIPrep-%s, and a newer version of dMRIPrep is available: %s.
Please check out our documentation about how and when to upgrade:
https://dmriprep.readthedocs.io/en/latest/faq.html#upgrading""" % (current, latest)

    assert (msg in captured) is expectation


@pytest.mark.parametrize('flagged', [
    (True, None),
    (True, 'random reason'),
    (False, None),
])
def test_get_parser_blacklist(monkeypatch, capsys, flagged):
    """Make sure the blacklisting banner is shown."""
    def _mock_is_bl(*args, **kwargs):
        return flagged

    monkeypatch.setattr(_version, 'is_flagged', _mock_is_bl)

    get_parser()
    captured = capsys.readouterr().err

    assert ('FLAGGED' in captured) is flagged[0]
    if flagged[0]:
        assert ((flagged[1] or 'reason: unknown') in captured)

def test_check_deps(input_dir_tree):
    from dmriprep.cli.run import build_workflow
    from pathlib import Path
    import logging
    import os
    import sys
    from nipype import logging as nlogging
    from multiprocessing import set_start_method, Process, Manager
    from dmriprep.utils.bids import write_derivative_description, validate_input_dir

    tmp_path, data = input_dir_tree

    set_start_method('forkserver')
    sys.argv=[str(tmp_path),str(tmp_path)+'/derivatives',"participant"]
    opts = get_parser().parse_args(sys.argv)

    exec_env = os.name

    # special variable set in the container
    if os.getenv('IS_DOCKER_8395080871'):
        exec_env = 'singularity'
        cgroup = Path('/proc/1/cgroup')
        if cgroup.exists() and 'docker' in cgroup.read_text():
            exec_env = 'docker'
            if os.getenv('DOCKER_VERSION_8395080871'):
                exec_env = 'dmriprep-docker'

    #sentry_sdk = None
    #if not opts.notrack:
    #    import sentry_sdk
    #    from dmriprep.utils.sentry import sentry_setup
    #    sentry_setup(opts, exec_env)

    # Validate inputs
    if not opts.skip_bids_validation:
        print("Making sure the input data is BIDS compliant (warnings can be ignored in most "
              "cases).")
        validate_input_dir(exec_env, opts.bids_dir, opts.participant_label)

    # FreeSurfer license
    default_license = str(Path(os.getenv('FREESURFER_HOME')) / 'license.txt')
    # Precedence: --fs-license-file, $FS_LICENSE, default_license
    license_file = opts.fs_license_file or Path(os.getenv('FS_LICENSE', default_license))
    if not license_file.exists():
        raise RuntimeError("""\
ERROR: a valid license file is required for FreeSurfer to run. dMRIPrep looked for an existing \
license file at several paths, in this order: 1) command line argument ``--fs-license-file``; \
2) ``$FS_LICENSE`` environment variable; and 3) the ``$FREESURFER_HOME/license.txt`` path. Get it \
(for free) by registering at https://surfer.nmr.mgh.harvard.edu/registration.html""")
    os.environ['FS_LICENSE'] = str(license_file.resolve())

    # Retrieve logging level
    log_level = int(max(25 - 5 * opts.verbose_count, logging.DEBUG))
    # Set logging
    logger = logging.getLogger('cli')
    logger.setLevel(log_level)
    nlogging.getLogger('nipype.workflow').setLevel(log_level)
    nlogging.getLogger('nipype.interface').setLevel(log_level)
    nlogging.getLogger('nipype.utils').setLevel(log_level)

    # Call build_workflow(opts, retval)
    with Manager() as mgr:
        retval = mgr.dict()
        p = Process(target=build_workflow, args=(opts, retval))
        p.start()
        p.join()

        retcode = p.exitcode or retval.get('return_code', 0)
        bids_dir = Path(retval.get('bids_dir'))
        output_dir = Path(retval.get('output_dir'))
        work_dir = Path(retval.get('work_dir'))
        plugin_settings = retval.get('plugin_settings', None)
        subject_list = retval.get('subject_list', None)
        dmriprep_wf = retval.get('workflow', None)
        run_uuid = retval.get('run_uuid', None)

    if opts.reports_only:
        sys.exit(int(retcode > 0))

    if opts.boilerplate:
        sys.exit(int(retcode > 0))

    if dmriprep_wf and opts.write_graph:
        dmriprep_wf.write_graph(graph2use="colored", format='svg', simple_form=True)

    retcode = retcode or int(dmriprep_wf is None)
    if retcode != 0:
        sys.exit(retcode)

    # Check workflow for missing commands
    missing = check_deps(dmriprep_wf)
    assert missing==[]