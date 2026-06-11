# tests/unit/plugins/modules/test_investigate.py
import pytest
from unittest.mock import patch, MagicMock
from ...conftest import set_module_args, AnsibleExitJson, AnsibleFailJson

REQUIRED_ARGS = {
    'neubird_url': 'https://nb.example.com',
    'neubird_username': 'user@test.com',
    'neubird_password': 'secret',
    'neubird_project': 'Red Hat',
    'context': {'cluster': 'prod-eks-01', 'node3': 'NotReady'},
}

FAKE_SESSION = {
    'session_uuid': 'sess-abc123',
    'investigation_status': 'INVESTIGATION_STATUS_IN_PROGRESS',
}

FAKE_SESSION_COMPLETED = {
    'session_uuid': 'sess-abc123',
    'investigation_status': 'INVESTIGATION_STATUS_COMPLETED',
}


def test_investigate_fire_and_forget(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigate
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_project_uuid', return_value='proj-uuid'), \
         patch.object(neubird_client, 'trigger_investigation', return_value=None) as mock_trigger, \
         patch.object(neubird_client, 'wait_for_investigation') as mock_wait, \
         patch.object(neubird_client, 'get_session_by_time', return_value=FAKE_SESSION), \
         patch('ansible_collections.neubird.aap.plugins.modules.investigate.time') as mock_time:
        mock_time.sleep = MagicMock()
        with pytest.raises(AnsibleExitJson) as exc:
            investigate.main()
    result = exc.value.args[0]
    assert result['changed'] is False
    assert result['session_uuid'] == 'sess-abc123'
    assert result['status'] == 'INVESTIGATION_STATUS_IN_PROGRESS'
    assert 'summary_sections' not in result
    mock_trigger.assert_called_once()
    mock_wait.assert_not_called()


def test_investigate_wait_mode_returns_summary(patch_ansible):
    set_module_args({**REQUIRED_ARGS, 'wait': True})
    from ansible_collections.neubird.aap.plugins.modules import investigate
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_metadata = {
        'session_metadata': {
            'confidence': 88.0,
            'elapsed_time_seconds': '204',
            'steps': 12,
            'total_actions': 35,
        }
    }
    fake_summary = {
        'sections': [
            {'title': 'Executive Summary', 'content': 'Cluster healthy.'},
        ]
    }
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_project_uuid', return_value='proj-uuid'), \
         patch.object(neubird_client, 'trigger_investigation', return_value=None), \
         patch.object(neubird_client, 'wait_for_investigation', return_value=None) as mock_wait, \
         patch.object(neubird_client, 'get_session_by_time', return_value=FAKE_SESSION_COMPLETED), \
         patch.object(neubird_client, 'get_session_metadata', return_value=fake_metadata), \
         patch.object(neubird_client, 'get_session_summary', return_value=fake_summary), \
         patch('ansible_collections.neubird.aap.plugins.modules.investigate.time') as mock_time:
        mock_time.sleep = MagicMock()
        with pytest.raises(AnsibleExitJson) as exc:
            investigate.main()
    result = exc.value.args[0]
    assert result['session_uuid'] == 'sess-abc123'
    assert result['confidence'] == 88.0
    assert result['elapsed_seconds'] == 204
    assert result['summary_sections'] == fake_summary['sections']
    mock_wait.assert_called_once()


def test_investigate_project_not_found(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigate
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_project_uuid', return_value=None):
        with pytest.raises(AnsibleFailJson) as exc:
            investigate.main()
    assert 'not found' in exc.value.args[0]['msg']
    assert 'Red Hat' in exc.value.args[0]['msg']


def test_investigate_auth_failure(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigate
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', side_effect=Exception('401 Unauthorized')):
        with pytest.raises(AnsibleFailJson) as exc:
            investigate.main()
    assert 'Authentication failed' in exc.value.args[0]['msg']


def test_investigate_session_not_retrievable(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import investigate
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    with patch.object(neubird_client, 'login', return_value='tok'), \
         patch.object(neubird_client, 'get_project_uuid', return_value='proj-uuid'), \
         patch.object(neubird_client, 'trigger_investigation', return_value=None), \
         patch.object(neubird_client, 'get_session_by_time', return_value=None), \
         patch('ansible_collections.neubird.aap.plugins.modules.investigate.time') as mock_time:
        mock_time.sleep = MagicMock()
        with pytest.raises(AnsibleFailJson) as exc:
            investigate.main()
    assert 'session UUID could not be retrieved' in exc.value.args[0]['msg']


def test_build_prompt_with_dict():
    from ansible_collections.neubird.aap.plugins.modules.investigate import build_prompt
    ctx = {'node': 'Node-3', 'status': 'NotReady'}
    result = build_prompt(ctx, 'Investigate the following context')
    assert result.startswith('Investigate the following context:\n\n')
    assert '"node"' in result
    assert '"Node-3"' in result


def test_build_prompt_with_string():
    from ansible_collections.neubird.aap.plugins.modules.investigate import build_prompt
    result = build_prompt('Node-3 is NotReady', 'Investigate the following context')
    assert result == 'Investigate the following context:\n\nNode-3 is NotReady'
