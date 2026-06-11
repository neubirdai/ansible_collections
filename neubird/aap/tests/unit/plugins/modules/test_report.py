# tests/unit/plugins/modules/test_report.py
import pytest
from ...conftest import set_module_args, AnsibleExitJson, AnsibleFailJson


def test_report_remediated(patch_ansible):
    set_module_args({'status': 'remediated'})
    from ansible_collections.neubird.aap.plugins.modules import report
    with pytest.raises(AnsibleExitJson) as exc:
        report.main()
    r = exc.value.args[0]
    assert r['changed'] is False
    assert r['neubird_report']['status'] == 'remediated'
    assert r['neubird_report']['schema_version'] == '1.0'
    assert 'timestamp' in r['neubird_report']


def test_report_with_investigation_id(patch_ansible):
    set_module_args({
        'status': 'remediated',
        'investigation_id': 'inv-1234',
        'changed_resources': ['sg-abc123'],
        'detail': {'key': 'value'},
    })
    from ansible_collections.neubird.aap.plugins.modules import report
    with pytest.raises(AnsibleExitJson) as exc:
        report.main()
    r = exc.value.args[0]['neubird_report']
    assert r['investigation_id'] == 'inv-1234'
    assert r['changed_resources'] == ['sg-abc123']
    assert r['detail'] == {'key': 'value'}


def test_report_no_change(patch_ansible):
    set_module_args({'status': 'no_change'})
    from ansible_collections.neubird.aap.plugins.modules import report
    with pytest.raises(AnsibleExitJson) as exc:
        report.main()
    assert exc.value.args[0]['neubird_report']['status'] == 'no_change'


def test_report_failed_status(patch_ansible):
    set_module_args({'status': 'failed'})
    from ansible_collections.neubird.aap.plugins.modules import report
    with pytest.raises(AnsibleExitJson) as exc:
        report.main()
    assert exc.value.args[0]['neubird_report']['status'] == 'failed'


def test_report_invalid_status(patch_ansible):
    set_module_args({'status': 'invalid'})
    from ansible_collections.neubird.aap.plugins.modules import report
    with pytest.raises(AnsibleFailJson):
        report.main()


def test_build_report_structure():
    from ansible_collections.neubird.aap.plugins.modules.report import build_report
    r = build_report('inv-1', 'remediated', ['sg-1'], {'k': 'v'})
    assert r['schema_version'] == '1.0'
    assert r['investigation_id'] == 'inv-1'
    assert r['status'] == 'remediated'
    assert r['changed_resources'] == ['sg-1']
    assert r['detail'] == {'k': 'v'}
    assert len(r['timestamp']) == 20  # YYYY-MM-DDTHH:MM:SSZ
