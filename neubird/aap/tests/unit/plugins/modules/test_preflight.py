# tests/unit/plugins/modules/test_preflight.py
import datetime
import pytest
from unittest.mock import patch
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson


def test_preflight_passes_with_no_checks(patch_ansible):
    set_module_args({})
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with pytest.raises(AnsibleExitJson) as exc:
        preflight.main()
    assert exc.value.args[0]['changed'] is False
    assert exc.value.args[0]['checks'] == {}


def test_preflight_maintenance_window_outside(patch_ansible):
    set_module_args({
        'check_maintenance_window': True,
        'maintenance_window_start': '02:00',
        'maintenance_window_end': '04:00',
    })
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'check_maintenance_window', return_value=False):
        with pytest.raises(AnsibleExitJson) as exc:
            preflight.main()
    assert exc.value.args[0]['checks']['maintenance_window'] == 'pass'


def test_preflight_maintenance_window_inside(patch_ansible):
    set_module_args({
        'check_maintenance_window': True,
        'maintenance_window_start': '02:00',
        'maintenance_window_end': '04:00',
    })
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'check_maintenance_window', return_value=True):
        with pytest.raises(AnsibleFailJson) as exc:
            preflight.main()
    assert exc.value.args[0]['neubird_preflight_failed'] is True
    assert exc.value.args[0]['checks']['maintenance_window'] == 'fail'


def test_preflight_maintenance_window_missing_params(patch_ansible):
    set_module_args({'check_maintenance_window': True})
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with pytest.raises(AnsibleFailJson) as exc:
        preflight.main()
    assert 'maintenance_window_start' in exc.value.args[0]['msg']


def test_preflight_host_reachable(patch_ansible):
    set_module_args({'target_host': '127.0.0.1'})
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'check_host_reachable', return_value=True):
        with pytest.raises(AnsibleExitJson) as exc:
            preflight.main()
    assert exc.value.args[0]['checks']['target_host'] == 'pass'


def test_preflight_host_unreachable(patch_ansible):
    set_module_args({'target_host': '10.255.255.1'})
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'check_host_reachable', return_value=False):
        with pytest.raises(AnsibleFailJson) as exc:
            preflight.main()
    assert exc.value.args[0]['checks']['target_host'] == 'fail'


def test_check_maintenance_window_inside():
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    assert check_maintenance_window('02:00', '04:00', datetime.time(3, 0)) is True


def test_check_maintenance_window_outside():
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    assert check_maintenance_window('02:00', '04:00', datetime.time(10, 0)) is False


def test_check_maintenance_window_overnight():
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    # 22:00 to 02:00 window — 23:30 is inside
    assert check_maintenance_window('22:00', '02:00', datetime.time(23, 30)) is True
    # 22:00 to 02:00 window — 10:00 is outside
    assert check_maintenance_window('22:00', '02:00', datetime.time(10, 0)) is False


def test_preflight_conflicting_jobs_pass(patch_ansible):
    set_module_args({
        'check_conflicting_jobs': True,
        'controller_host': 'https://aap.example.com',
        'controller_token': 'fake-token',
        'template_name': 'Rotate IAM Key',
    })
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'get_running_job_count', return_value=0):
        with pytest.raises(AnsibleExitJson) as exc:
            preflight.main()
    assert exc.value.args[0]['checks']['conflicting_jobs'] == 'pass'


def test_preflight_conflicting_jobs_fail(patch_ansible):
    set_module_args({
        'check_conflicting_jobs': True,
        'controller_host': 'https://aap.example.com',
        'controller_token': 'fake-token',
        'template_name': 'Rotate IAM Key',
    })
    from ansible_collections.neubird.aap.plugins.modules import preflight
    with patch.object(preflight, 'get_running_job_count', return_value=2):
        with pytest.raises(AnsibleFailJson) as exc:
            preflight.main()
    assert exc.value.args[0]['checks']['conflicting_jobs'] == 'fail'
    assert exc.value.args[0]['neubird_preflight_failed'] is True
