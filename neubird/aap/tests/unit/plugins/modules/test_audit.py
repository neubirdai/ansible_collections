# tests/unit/plugins/modules/test_audit.py
import pytest
from unittest.mock import patch
from ...conftest import set_module_args, AnsibleExitJson, AnsibleFailJson


def test_audit_stdout(patch_ansible):
    set_module_args({'action': 'iam_key_disabled', 'triggered_by': 'neubird_ai'})
    from ansible_collections.neubird.aap.plugins.modules import audit
    with patch.object(audit, 'write_stdout') as mock_write:
        with pytest.raises(AnsibleExitJson) as exc:
            audit.main()
    mock_write.assert_called_once()
    record = mock_write.call_args[0][0]
    assert record['action'] == 'iam_key_disabled'
    assert record['triggered_by'] == 'neubird_ai'
    assert record['schema_version'] == '1.0'
    assert 'timestamp' in record


def test_audit_with_investigation_id(patch_ansible):
    set_module_args({
        'action': 'sg_rule_removed',
        'triggered_by': 'neubird_ai',
        'investigation_id': 'inv-1234',
    })
    from ansible_collections.neubird.aap.plugins.modules import audit
    with patch.object(audit, 'write_stdout') as mock_write:
        with pytest.raises(AnsibleExitJson):
            audit.main()
    mock_write.assert_called_once()
    record = mock_write.call_args[0][0]
    assert record['investigation_id'] == 'inv-1234'


def test_audit_syslog_destination(patch_ansible):
    set_module_args({
        'action': 'key_rotated',
        'triggered_by': 'neubird_ai',
        'destination': 'syslog',
    })
    from ansible_collections.neubird.aap.plugins.modules import audit
    with patch.object(audit, 'write_syslog') as mock_write:
        with pytest.raises(AnsibleExitJson):
            audit.main()
    mock_write.assert_called_once()
    record = mock_write.call_args[0][0]
    assert record['action'] == 'key_rotated'


def test_audit_webhook_destination(patch_ansible):
    set_module_args({
        'action': 'key_rotated',
        'triggered_by': 'neubird_ai',
        'destination': 'webhook',
        'webhook_url': 'https://audit.example.com/events',
    })
    from ansible_collections.neubird.aap.plugins.modules import audit
    with patch.object(audit, 'write_webhook') as mock_write:
        with pytest.raises(AnsibleExitJson):
            audit.main()
    mock_write.assert_called_once()
    assert mock_write.call_args[0][1] == 'https://audit.example.com/events'


def test_audit_webhook_missing_url(patch_ansible):
    set_module_args({
        'action': 'key_rotated',
        'triggered_by': 'neubird_ai',
        'destination': 'webhook',
    })
    from ansible_collections.neubird.aap.plugins.modules import audit
    with pytest.raises(AnsibleFailJson) as exc:
        audit.main()
    assert 'webhook_url' in exc.value.args[0]['msg']


def test_audit_check_mode(patch_ansible):
    set_module_args({
        'action': 'key_rotated',
        'triggered_by': 'neubird_ai',
        '_ansible_check_mode': True,
    })
    from ansible_collections.neubird.aap.plugins.modules import audit
    with patch.object(audit, 'write_stdout') as mock_write:
        with pytest.raises(AnsibleExitJson) as exc:
            audit.main()
    mock_write.assert_not_called()
    assert exc.value.args[0]['changed'] is False


def test_build_record_structure():
    from ansible_collections.neubird.aap.plugins.modules.audit import build_record
    r = build_record('iam_key_disabled', 'neubird_ai', 'inv-1')
    assert r['schema_version'] == '1.0'
    assert r['action'] == 'iam_key_disabled'
    assert r['triggered_by'] == 'neubird_ai'
    assert r['investigation_id'] == 'inv-1'
    assert len(r['timestamp']) == 20
