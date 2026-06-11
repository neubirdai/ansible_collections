# tests/unit/plugins/module_utils/test_neubird_client.py
import json
import pytest
from unittest.mock import patch, MagicMock


def _mock_response(body, status=200):
    """Return an open_url response mock that yields body bytes line by line."""
    mock = MagicMock()
    mock.read.return_value = json.dumps(body).encode('utf-8')
    # For SSE iteration: yield lines as bytes
    mock.__iter__ = MagicMock(return_value=iter([]))
    return mock


def test_login_returns_access_token():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_resp = _mock_response({'access_token': 'tok-123', 'token_type': 'Bearer'})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp) as mock_open:
        token = neubird_client.login('https://nb.example.com', 'user@test.com', 'secret')
    assert token == 'tok-123'
    call_args = mock_open.call_args
    assert '/api/v1/user/login' in call_args[0][0]
    body = json.loads(call_args[1]['data'])
    assert body['email'] == 'user@test.com'
    assert body['password'] == 'secret'


def test_get_project_uuid_found():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_resp = _mock_response({'specs': [
        {'name': 'Other Project', 'uuid': 'uuid-other'},
        {'name': 'Red Hat', 'uuid': 'uuid-rh'},
    ]})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp):
        result = neubird_client.get_project_uuid('https://nb.example.com', 'tok', 'Red Hat')
    assert result == 'uuid-rh'


def test_get_project_uuid_not_found():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_resp = _mock_response({'specs': [{'name': 'Other', 'uuid': 'uuid-other'}]})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp):
        result = neubird_client.get_project_uuid('https://nb.example.com', 'tok', 'Red Hat')
    assert result is None


def test_get_project_uuid_empty_specs():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_resp = _mock_response({'specs': []})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp):
        result = neubird_client.get_project_uuid('https://nb.example.com', 'tok', 'Red Hat')
    assert result is None


def test_trigger_investigation_posts_correct_body():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    sse_lines = [
        b'id: 1-0\n',
        b'event: falcon\n',
        b'data: {"type": "phase", "phase": "investigating"}\n',
        b'\n',
        b'id: 2-0\n',
        b'event: falcon\n',
        b'data: {"type": "session_metadata", "status": "INVESTIGATION_STATUS_IN_PROGRESS", "confidence": 30}\n',
        b'\n',
    ]
    mock_resp = MagicMock()
    mock_resp.__iter__ = MagicMock(return_value=iter(sse_lines))
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=mock_resp) as mock_open:
        neubird_client.trigger_investigation(
            'https://nb.example.com', 'tok', 'proj-uuid', 'Investigate EKS health'
        )
    call_args = mock_open.call_args
    assert '/api/v1/inference/session' in call_args[0][0]
    body = json.loads(call_args[1]['data'])
    assert body['action'] == 'ACTION_NEXT'
    assert body['session_mode'] == 'SESSION_MODE_CHAT'
    assert body['session_type'] == 'SESSION_TYPE_USER'
    assert body['session_origin'] == 'SESSION_ORIGIN_AUTOMATED'
    assert body['messages'][0]['content']['content_type'] == 'CONTENT_TYPE_CHAT_PROMPT'
    assert body['messages'][0]['content']['parts'] == ['Investigate EKS health']
    assert body['project_uuid'] == 'proj-uuid'


def test_get_session_by_time_returns_first():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    sessions = [
        {'session_uuid': 'uuid-new', 'investigation_status': 'INVESTIGATION_STATUS_IN_PROGRESS'},
        {'session_uuid': 'uuid-old', 'investigation_status': 'INVESTIGATION_STATUS_COMPLETED'},
    ]
    fake_resp = _mock_response({'sessions': sessions, 'pagination': {'total': 2}})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp):
        result = neubird_client.get_session_by_time(
            'https://nb.example.com', 'tok', 'proj-uuid', '2026-06-01T12:00:00Z'
        )
    assert result['session_uuid'] == 'uuid-new'


def test_get_session_by_time_empty_returns_none():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    fake_resp = _mock_response({'sessions': [], 'pagination': {'total': 0}})
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp):
        result = neubird_client.get_session_by_time(
            'https://nb.example.com', 'tok', 'proj-uuid', '2026-06-01T12:00:00Z'
        )
    assert result is None


def test_get_session_metadata():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    body = {
        'name': 'EKS Investigation',
        'session_metadata': {
            'investigation_status': 'INVESTIGATION_STATUS_COMPLETED',
            'confidence': 88.0,
            'elapsed_time_seconds': '204',
            'steps': 12,
            'total_actions': 35,
        }
    }
    fake_resp = _mock_response(body)
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp) as mock_open:
        result = neubird_client.get_session_metadata('https://nb.example.com', 'tok', 'sess-uuid')
    assert result['session_metadata']['confidence'] == 88.0
    assert '/api/v2/inference/session/metadata/sess-uuid' in mock_open.call_args[0][0]


def test_get_session_summary():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    body = {
        'summary_sections': {
            'session_uuid': 'sess-uuid',
            'sections': [
                {'title': 'Executive Summary', 'content': 'All good.'},
                {'title': 'Remediation Plan', 'content': 'No action needed.'},
            ],
        }
    }
    fake_resp = _mock_response(body)
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=fake_resp) as mock_open:
        result = neubird_client.get_session_summary('https://nb.example.com', 'tok', 'sess-uuid')
    assert result['sections'][0]['title'] == 'Executive Summary'
    assert '/api/v2/inference/session/summary/sess-uuid' in mock_open.call_args[0][0]


def test_trigger_investigation_raises_on_stream_end():
    from ansible_collections.neubird.aap.plugins.module_utils import neubird_client
    # Stream ends without a session_metadata event
    sse_lines = [
        b'data: {"type": "phase"}\n',
        b'\n',
    ]
    mock_resp = MagicMock()
    mock_resp.__iter__ = MagicMock(return_value=iter(sse_lines))
    with patch('ansible_collections.neubird.aap.plugins.module_utils.neubird_client.open_url',
               return_value=mock_resp):
        with pytest.raises(Exception, match='SSE stream ended'):
            neubird_client.trigger_investigation(
                'https://nb.example.com', 'tok', 'proj-uuid', 'test'
            )
