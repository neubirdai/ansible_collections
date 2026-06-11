# tests/unit/plugins/modules/test_investigation_result.py
import pytest
from unittest.mock import patch
from ...conftest import set_module_args, AnsibleExitJson, AnsibleFailJson

REQUIRED_ARGS = {
    'neubird_url': 'https://nb.example.com',
    'neubird_username': 'user@test.com',
    'neubird_password': 'secret',
    'session_uuid': 'sess-abc123',
}

FAKE_METADATA_COMPLETED = {
    'name': 'EKS Investigation',
    'session_metadata': {
        'investigation_status': 'INVESTIGATION_STATUS_COMPLETED',
        'confidence': 88.0,
        'elapsed_time_seconds': '204',
        'steps': 12,
        'total_actions': 35,
    }
}

FAKE_METADATA_IN_PROGRESS = {
    'name': 'EKS Investigation',
    'session_metadata': {
        'investigation_status': 'INVESTIGATION_STATUS_IN_PROGRESS',
        'confidence': 50.0,
        'elapsed_time_seconds': '30',
        'steps': 3,
        'total_actions': 10,
    }
}

FAKE_SUMMARY = {
    'sections': [
        {'title': 'Executive Summary', 'content': 'Cluster healthy.'},
        {'title': 'Remediation Plan', 'content': 'No action needed.'},
    ]
}


def test_investigation_result_completed(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigation_result
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_session_metadata', return_value=FAKE_METADATA_COMPLETED), \
         patch.object(neubird_client, 'get_session_summary', return_value=FAKE_SUMMARY) as mock_summary:
        with pytest.raises(AnsibleExitJson) as exc:
            investigation_result.main()
    result = exc.value.args[0]
    assert result['changed'] is False
    assert result['session_uuid'] == 'sess-abc123'
    assert result['status'] == 'INVESTIGATION_STATUS_COMPLETED'
    assert result['confidence'] == 88.0
    assert result['elapsed_seconds'] == 204
    assert result['steps'] == 12
    assert result['total_actions'] == 35
    assert result['summary_sections'] == FAKE_SUMMARY['sections']
    mock_summary.assert_called_once_with('https://nb.example.com', 'tok', 'sess-abc123')


def test_investigation_result_in_progress_no_summary(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigation_result
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_session_metadata', return_value=FAKE_METADATA_IN_PROGRESS), \
         patch.object(neubird_client, 'get_session_summary') as mock_summary:
        with pytest.raises(AnsibleExitJson) as exc:
            investigation_result.main()
    result = exc.value.args[0]
    assert result['status'] == 'INVESTIGATION_STATUS_IN_PROGRESS'
    assert 'summary_sections' not in result
    mock_summary.assert_not_called()


def test_investigation_result_stopped_returns_summary(patch_ansible):
    """STOPPED status should still fetch and return any summary that exists."""
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigation_result
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    stopped_metadata = {
        'name': 'EKS Investigation',
        'session_metadata': {
            'investigation_status': 'INVESTIGATION_STATUS_STOPPED',
            'confidence': 0.0,
            'elapsed_time_seconds': '10',
            'steps': 1,
            'total_actions': 2,
        }
    }
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_session_metadata', return_value=stopped_metadata), \
         patch.object(neubird_client, 'get_session_summary', return_value=FAKE_SUMMARY):
        with pytest.raises(AnsibleExitJson) as exc:
            investigation_result.main()
    result = exc.value.args[0]
    assert result['status'] == 'INVESTIGATION_STATUS_STOPPED'
    assert 'summary_sections' in result


def test_investigation_result_auth_failure(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigation_result
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', side_effect=Exception('401 Unauthorized')):
        with pytest.raises(AnsibleFailJson) as exc:
            investigation_result.main()
    assert 'Authentication failed' in exc.value.args[0]['msg']


def test_investigation_result_session_not_found(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigation_result
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_session_metadata', side_effect=Exception('404 Not Found')):
        with pytest.raises(AnsibleFailJson) as exc:
            investigation_result.main()
    assert 'Failed to retrieve session' in exc.value.args[0]['msg']
