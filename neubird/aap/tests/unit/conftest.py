# tests/unit/conftest.py
import json
import pytest
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


def set_module_args(args):
    """Inject module arguments for AnsibleModule to pick up in tests."""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)
    basic._ANSIBLE_PROFILE = 'legacy'


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


@pytest.fixture
def patch_ansible(monkeypatch):
    def exit_json(self, **kwargs):
        raise AnsibleExitJson(kwargs)

    def fail_json(self, **kwargs):
        raise AnsibleFailJson(kwargs)

    monkeypatch.setattr(basic.AnsibleModule, 'exit_json', exit_json)
    monkeypatch.setattr(basic.AnsibleModule, 'fail_json', fail_json)
