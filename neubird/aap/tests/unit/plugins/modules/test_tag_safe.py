# tests/unit/plugins/modules/test_tag_safe.py
import json
import pytest
from unittest.mock import patch
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson

REQUIRED_ARGS = {
    'controller_host': 'https://aap.example.com',
    'controller_token': 'fake-token',
    'template_name': 'Rotate IAM Key',
}

FAKE_TEMPLATE = {
    'id': 42,
    'name': 'Rotate IAM Key',
    'extra_vars': '{}',
}


def test_tag_safe_tags_template(patch_ansible):
    set_module_args({**REQUIRED_ARGS, 'environments': ['dev'], 'max_auto_runs_per_hour': 5})
    from ansible_collections.neubird.aap.plugins.modules import tag_safe
    with patch.object(tag_safe, 'get_template', return_value=FAKE_TEMPLATE):
        with patch.object(tag_safe, 'patch_template_extra_vars', return_value={}) as mock_patch:
            with pytest.raises(AnsibleExitJson) as exc:
                tag_safe.main()
    result = exc.value.args[0]
    assert result['changed'] is True
    assert result['template_id'] == 42
    assert result['neubird_safe_tag']['version'] == '1.0'
    assert result['neubird_safe_tag']['environments'] == ['dev']
    assert result['neubird_safe_tag']['max_auto_runs_per_hour'] == 5
    mock_patch.assert_called_once()


def test_tag_safe_template_not_found(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import tag_safe
    with patch.object(tag_safe, 'get_template', return_value=None):
        with pytest.raises(AnsibleFailJson) as exc:
            tag_safe.main()
    assert 'not found' in exc.value.args[0]['msg']


def test_tag_safe_no_change_when_identical(patch_ansible):
    existing_tag = {'version': '1.0', 'tagged_at': '2020-01-01T00:00:00Z'}
    template = {
        'id': 42,
        'name': 'Rotate IAM Key',
        'extra_vars': json.dumps({'_neubird_safe': existing_tag}),
    }
    set_module_args(REQUIRED_ARGS)  # no environments/requires_approval_in/max — same as existing_tag
    from ansible_collections.neubird.aap.plugins.modules import tag_safe
    with patch.object(tag_safe, 'get_template', return_value=template):
        with patch.object(tag_safe, 'patch_template_extra_vars') as mock_patch:
            with pytest.raises(AnsibleExitJson) as exc:
                tag_safe.main()
    assert exc.value.args[0]['changed'] is False
    mock_patch.assert_not_called()


def test_tag_safe_check_mode(patch_ansible):
    set_module_args({**REQUIRED_ARGS, '_ansible_check_mode': True})
    from ansible_collections.neubird.aap.plugins.modules import tag_safe
    with patch.object(tag_safe, 'get_template', return_value=FAKE_TEMPLATE):
        with patch.object(tag_safe, 'patch_template_extra_vars') as mock_patch:
            with pytest.raises(AnsibleExitJson) as exc:
                tag_safe.main()
    assert exc.value.args[0]['changed'] is True
    mock_patch.assert_not_called()


def test_build_safe_tag_structure():
    from ansible_collections.neubird.aap.plugins.modules.tag_safe import build_safe_tag
    tag = build_safe_tag(['dev'], ['prod'], 10)
    assert tag['version'] == '1.0'
    assert tag['environments'] == ['dev']
    assert tag['requires_approval_in'] == ['prod']
    assert tag['max_auto_runs_per_hour'] == 10
    assert 'tagged_at' in tag
