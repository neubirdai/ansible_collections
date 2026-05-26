# neubird.aap Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `neubird.aap` certified Ansible collection — 4 Python modules and 1 lookup plugin that make any AAP job template AI-aware for NeuBird investigations.

**Architecture:** All content lives in `/Users/alee/Desktop/Development/ansible_collections/neubird/aap/` (the collection root). The directory name satisfies ansible-test's FQCN requirement directly — no symlinks needed. Modules use only Python stdlib and `ansible.module_utils` (no pip dependencies, no collection dependencies). Each module is TDD: failing test → minimal implementation → passing test → commit.

**Tech Stack:** Python 3.13, ansible-core 2.20.6, ansible-test (sanity + units + integration), pytest 9, ansible-lint 26, galaxy-importer 0.4.39.

---

## File Map

| File | Purpose |
|---|---|
| `galaxy.yml` | Collection metadata, version, license |
| `meta/runtime.yml` | Minimum ansible-core version |
| `CHANGELOG.rst` | Required for certification |
| `README.md` | Installation + module reference |
| `plugins/modules/report.py` | `neubird.aap.report` module |
| `plugins/modules/tag_safe.py` | `neubird.aap.tag_safe` module |
| `plugins/modules/preflight.py` | `neubird.aap.preflight` module |
| `plugins/modules/audit.py` | `neubird.aap.audit` module |
| `plugins/lookup/context.py` | `neubird.aap.context` lookup plugin |
| `docs/{module}.md` | Per-module documentation (5 files) |
| `tests/unit/conftest.py` | Shared test helpers |
| `tests/unit/plugins/modules/test_report.py` | Unit tests for report |
| `tests/unit/plugins/modules/test_tag_safe.py` | Unit tests for tag_safe |
| `tests/unit/plugins/modules/test_preflight.py` | Unit tests for preflight |
| `tests/unit/plugins/modules/test_audit.py` | Unit tests for audit |
| `tests/unit/plugins/lookup/test_context.py` | Unit tests for context |
| `tests/integration/targets/report/tasks/main.yml` | Integration test for report |
| `tests/integration/targets/audit/tasks/main.yml` | Integration test for audit |
| `tests/integration/targets/context/tasks/main.yml` | Integration test for context |
| `tests/sanity/ignore.txt` | Sanity check ignores (if needed) |

---

## Task 1: Scaffold the collection

**Files:**
- Create: all directories and `galaxy.yml`, `meta/runtime.yml`, `CHANGELOG.rst`, `README.md`
- Create: `/Users/alee/Desktop/Development/ansible_collections/neubird/aap` symlink

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
mkdir -p plugins/modules plugins/lookup meta docs \
  tests/unit/plugins/modules tests/unit/plugins/lookup \
  tests/integration/targets/report/tasks \
  tests/integration/targets/audit/tasks \
  tests/integration/targets/context/tasks \
  tests/sanity
```

- [ ] **Step 2: Create `__init__.py` stubs for test discovery**

```bash
touch tests/unit/__init__.py \
      tests/unit/plugins/__init__.py \
      tests/unit/plugins/modules/__init__.py \
      tests/unit/plugins/lookup/__init__.py
```

- [ ] **Step 3: Create `galaxy.yml`**

```yaml
# galaxy.yml
namespace: neubird
name: aap
version: 1.0.0
readme: README.md
description: >
  Intelligence gateway between Ansible Automation Platform and NeuBird AI.
  Makes any AAP job template AI-aware with reporting, safety tagging,
  context injection, pre-flight gating, and audit logging.
license:
  - Apache-2.0
tags:
  - ai
  - automation
  - remediation
  - monitoring
  - neubird
  - aap
repository: https://github.com/neubird-ai/ansible-collection
documentation: https://github.com/neubird-ai/ansible-collection/blob/main/README.md
homepage: https://neubird.ai
issues: https://github.com/neubird-ai/ansible-collection/issues
build_ignore:
  - "*.tar.gz"
  - ".git"
  - ".gitignore"
  - "docs/superpowers"
```

- [ ] **Step 4: Create `meta/runtime.yml`**

```yaml
# meta/runtime.yml
requires_ansible: ">=2.16.0"
```

- [ ] **Step 5: Create `CHANGELOG.rst`**

```rst
================================
neubird.aap Release Notes
================================

.. contents:: Topics

v1.0.0
======

New Modules
-----------

- ``neubird.aap.report`` - Report remediation results to NeuBird AI.
- ``neubird.aap.tag_safe`` - Mark an AAP job template as safe for NeuBird automated remediation.
- ``neubird.aap.preflight`` - Run pre-flight safety checks before NeuBird-triggered jobs.
- ``neubird.aap.audit`` - Write a structured audit record for NeuBird-triggered remediation.

New Lookup Plugins
------------------

- ``neubird.aap.context`` - Read NeuBird investigation context from AAP job variables.
```

- [ ] **Step 6: Create `README.md`**

```markdown
# neubird.aap

Intelligence gateway between Ansible Automation Platform and NeuBird AI.

## Requirements

- ansible-core >= 2.16.0
- Python >= 3.9

## Installation

```bash
ansible-galaxy collection install neubird.aap
```

## Modules

| Module | Description |
|---|---|
| `neubird.aap.report` | Report remediation results to NeuBird AI |
| `neubird.aap.tag_safe` | Mark a job template as safe for automated remediation |
| `neubird.aap.preflight` | Pre-flight safety checks before automated job execution |
| `neubird.aap.audit` | Write structured audit records for compliance |

## Lookup Plugins

| Plugin | Description |
|---|---|
| `neubird.aap.context` | Read NeuBird investigation context from job variables |

## License

Apache-2.0
```

- [ ] **Step 7: Verify ansible-test finds the collection**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-test sanity --list-tests 2>&1 | head -10
```

Expected: list of sanity test names (validate-modules, pylint, etc.) — no "not in a collection" error.

- [ ] **Step 9: Initialize git and commit scaffold**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git init
git add galaxy.yml meta/ CHANGELOG.rst README.md
git commit -m "feat: scaffold neubird.aap collection"
```

---

## Task 2: `neubird.aap.report` module

**Files:**
- Create: `plugins/modules/report.py`
- Create: `tests/unit/plugins/modules/test_report.py`
- Create: `tests/unit/conftest.py`

- [ ] **Step 1: Create shared test helper `tests/unit/conftest.py`**

```python
# tests/unit/conftest.py
import json
import pytest
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


def set_module_args(args):
    """Inject module arguments for AnsibleModule to pick up in tests."""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


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
```

- [ ] **Step 2: Write failing unit tests `tests/unit/plugins/modules/test_report.py`**

```python
# tests/unit/plugins/modules/test_report.py
import json
import pytest
from unittest.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson, patch_ansible


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
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_report.py -v 2>&1 | tail -20
```

Expected: `ImportError` or `ModuleNotFoundError` — `report` module does not exist yet.

- [ ] **Step 4: Create `plugins/modules/report.py`**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: report
short_description: Report remediation results to NeuBird AI
version_added: "1.0.0"
description:
  - Surfaces structured job execution results in a format NeuBird AI can read
    through its MCP connection to Ansible Automation Platform.
  - Add this module near the end of any playbook NeuBird may trigger.
options:
  investigation_id:
    description:
      - NeuBird investigation ID. If omitted the report is standalone.
    type: str
    required: false
  status:
    description:
      - Remediation outcome.
    type: str
    required: true
    choices: ['remediated', 'failed', 'no_change']
  changed_resources:
    description:
      - List of resource identifiers that were modified.
    type: list
    elements: str
    required: false
    default: []
  detail:
    description:
      - Raw task result or any structured detail to pass through.
    type: dict
    required: false
    default: {}
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Report remediation result to NeuBird
  neubird.aap.report:
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    status: remediated
    changed_resources:
      - "sg-abc123"
    detail: "{{ remediation_result }}"
'''

RETURN = r'''
neubird_report:
  description: The structured report written to job output.
  type: dict
  returned: always
  sample:
    schema_version: "1.0"
    investigation_id: "inv-1234"
    status: "remediated"
    changed_resources: ["sg-abc123"]
    detail: {}
    timestamp: "2026-05-23T14:00:00Z"
'''

import datetime

from ansible.module_utils.basic import AnsibleModule


def build_report(investigation_id, status, changed_resources, detail):
    return {
        'schema_version': '1.0',
        'investigation_id': investigation_id,
        'status': status,
        'changed_resources': changed_resources,
        'detail': detail,
        'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            investigation_id=dict(type='str', required=False, default=None),
            status=dict(
                type='str',
                required=True,
                choices=['remediated', 'failed', 'no_change'],
            ),
            changed_resources=dict(type='list', elements='str', default=[]),
            detail=dict(type='dict', default={}),
        ),
        supports_check_mode=True,
    )

    report = build_report(
        investigation_id=module.params['investigation_id'],
        status=module.params['status'],
        changed_resources=module.params['changed_resources'],
        detail=module.params['detail'],
    )

    module.exit_json(changed=False, neubird_report=report)


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_report.py -v
```

Expected: 6 PASSED.

- [ ] **Step 6: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add plugins/modules/report.py tests/unit/conftest.py tests/unit/plugins/modules/test_report.py tests/unit/__init__.py tests/unit/plugins/__init__.py tests/unit/plugins/modules/__init__.py
git commit -m "feat: add neubird.aap.report module"
```

---

## Task 3: `neubird.aap.context` lookup plugin

**Files:**
- Create: `plugins/lookup/context.py`
- Create: `tests/unit/plugins/lookup/test_context.py`

- [ ] **Step 1: Write failing unit tests `tests/unit/plugins/lookup/test_context.py`**

```python
# tests/unit/plugins/lookup/test_context.py
import pytest


def test_context_returns_empty_when_no_vars():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables={})
    assert result == [{
        'investigation_id': None,
        'severity': None,
        'affected_resource': None,
        'triggered_by': None,
    }]


def test_context_returns_injected_values():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    ctx = {
        'investigation_id': 'inv-1234',
        'severity': 'high',
        'affected_resource': 'sg-abc123',
        'triggered_by': 'neubird_ai',
    }
    result = lookup.run([], variables={'_neubird_context': ctx})
    assert result == [ctx]


def test_context_fills_missing_keys():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables={'_neubird_context': {'investigation_id': 'inv-5'}})
    assert result[0]['investigation_id'] == 'inv-5'
    assert result[0]['severity'] is None
    assert result[0]['affected_resource'] is None
    assert result[0]['triggered_by'] is None


def test_context_graceful_with_none_variables():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables=None)
    assert result[0]['investigation_id'] is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/lookup/test_context.py -v 2>&1 | tail -10
```

Expected: `ImportError` — `context` module does not exist yet.

- [ ] **Step 3: Create `plugins/lookup/context.py`**

```python
# plugins/lookup/context.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
name: context
short_description: Read NeuBird investigation context from AAP job variables
version_added: "1.0.0"
description:
  - Returns the NeuBird investigation context injected by NeuBird AI when
    triggering an AAP job. Falls back gracefully when the job was not
    triggered by NeuBird (all keys are null).
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Load NeuBird investigation context
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Use context downstream
  debug:
    msg: "Remediating {{ neubird_ctx.affected_resource }} for investigation {{ neubird_ctx.investigation_id }}"
'''

RETURN = r'''
_raw:
  description: NeuBird investigation context dict.
  type: list
  elements: dict
  returned: always
  sample:
    - investigation_id: "inv-1234"
      severity: "high"
      affected_resource: "sg-abc123"
      triggered_by: "neubird_ai"
'''

from ansible.plugins.lookup import LookupBase

_EMPTY_CONTEXT = {
    'investigation_id': None,
    'severity': None,
    'affected_resource': None,
    'triggered_by': None,
}


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}
        injected = variables.get('_neubird_context', {}) or {}
        result = dict(_EMPTY_CONTEXT)
        result.update(injected)
        return [result]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/lookup/test_context.py -v
```

Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add plugins/lookup/context.py tests/unit/plugins/lookup/__init__.py tests/unit/plugins/lookup/test_context.py
git commit -m "feat: add neubird.aap.context lookup plugin"
```

---

## Task 4: `neubird.aap.preflight` module

**Files:**
- Create: `plugins/modules/preflight.py`
- Create: `tests/unit/plugins/modules/test_preflight.py`

- [ ] **Step 1: Write failing unit tests `tests/unit/plugins/modules/test_preflight.py`**

```python
# tests/unit/plugins/modules/test_preflight.py
import pytest
from unittest.mock import patch, MagicMock
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson, patch_ansible


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
    import datetime
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    assert check_maintenance_window('02:00', '04:00', datetime.time(3, 0)) is True


def test_check_maintenance_window_outside():
    import datetime
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    assert check_maintenance_window('02:00', '04:00', datetime.time(10, 0)) is False


def test_check_maintenance_window_overnight():
    import datetime
    from ansible_collections.neubird.aap.plugins.modules.preflight import check_maintenance_window
    # 22:00 to 02:00 window — 23:30 is inside
    assert check_maintenance_window('22:00', '02:00', datetime.time(23, 30)) is True
    # 22:00 to 02:00 window — 10:00 is outside
    assert check_maintenance_window('22:00', '02:00', datetime.time(10, 0)) is False
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_preflight.py -v 2>&1 | tail -10
```

Expected: `ImportError` — `preflight` module does not exist yet.

- [ ] **Step 3: Create `plugins/modules/preflight.py`**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: preflight
short_description: Run pre-flight safety checks before NeuBird-triggered jobs
version_added: "1.0.0"
description:
  - Validates that conditions are safe before NeuBird auto-runs a job.
  - Fails the play with a structured error NeuBird can parse via MCP.
  - Place as the first task in any playbook tagged for automated remediation.
options:
  check_maintenance_window:
    description:
      - Fail if current UTC time falls within the defined maintenance window.
    type: bool
    required: false
    default: false
  maintenance_window_start:
    description:
      - Start of maintenance window in HH:MM UTC format.
        Required when check_maintenance_window is true.
    type: str
    required: false
  maintenance_window_end:
    description:
      - End of maintenance window in HH:MM UTC format.
        Required when check_maintenance_window is true.
    type: str
    required: false
  check_conflicting_jobs:
    description:
      - Fail if another job using the same template is currently running.
        Requires controller_host, controller_token, and template_name.
    type: bool
    required: false
    default: false
  controller_host:
    description:
      - AAP controller base URL. Required when check_conflicting_jobs is true.
    type: str
    required: false
  controller_token:
    description:
      - AAP controller OAuth token. Required when check_conflicting_jobs is true.
    type: str
    required: false
    no_log: true
  template_name:
    description:
      - Job template name to check for conflicts.
        Required when check_conflicting_jobs is true.
    type: str
    required: false
  target_host:
    description:
      - Hostname or IP to verify is reachable on port 22 before proceeding.
    type: str
    required: false
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Run pre-flight safety checks
  neubird.aap.preflight:
    check_maintenance_window: true
    maintenance_window_start: "02:00"
    maintenance_window_end: "04:00"
    check_conflicting_jobs: true
    controller_host: "https://aap.example.com"
    controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
    template_name: "Rotate IAM Key"
    target_host: "{{ inventory_hostname }}"
'''

RETURN = r'''
checks:
  description: Results of each check that was run.
  type: dict
  returned: always
  sample:
    maintenance_window: "pass"
    conflicting_jobs: "pass"
    target_host: "pass"
'''

import datetime
import json
import socket

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


def check_maintenance_window(start_str, end_str, current_time=None):
    if current_time is None:
        current_time = datetime.datetime.utcnow().time()
    start = datetime.time(*[int(x) for x in start_str.split(':')])
    end = datetime.time(*[int(x) for x in end_str.split(':')])
    if start <= end:
        return start <= current_time <= end
    return current_time >= start or current_time <= end


def check_host_reachable(hostname, port=22, timeout=5):
    try:
        socket.setdefaulttimeout(timeout)
        with socket.create_connection((hostname, port)):
            return True
    except (socket.timeout, socket.error):
        return False


def get_running_job_count(controller_host, controller_token, template_name):
    url = '{0}/api/v2/jobs/?status=running&job_template__name={1}'.format(
        controller_host.rstrip('/'), template_name
    )
    response = open_url(
        url,
        headers={
            'Authorization': 'Bearer {0}'.format(controller_token),
            'Content-Type': 'application/json',
        },
        method='GET',
        validate_certs=True,
    )
    data = json.loads(response.read())
    return data.get('count', 0)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            check_maintenance_window=dict(type='bool', default=False),
            maintenance_window_start=dict(type='str', required=False),
            maintenance_window_end=dict(type='str', required=False),
            check_conflicting_jobs=dict(type='bool', default=False),
            controller_host=dict(type='str', required=False),
            controller_token=dict(type='str', required=False, no_log=True),
            template_name=dict(type='str', required=False),
            target_host=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )

    params = module.params
    checks = {}
    failures = []

    if params['check_maintenance_window']:
        if not params['maintenance_window_start'] or not params['maintenance_window_end']:
            module.fail_json(
                msg='maintenance_window_start and maintenance_window_end are required '
                    'when check_maintenance_window is true',
                neubird_preflight_failed=True,
                checks=checks,
            )
        in_window = check_maintenance_window(
            params['maintenance_window_start'],
            params['maintenance_window_end'],
        )
        checks['maintenance_window'] = 'fail' if in_window else 'pass'
        if in_window:
            failures.append(
                'Currently inside maintenance window ({0} to {1} UTC)'.format(
                    params['maintenance_window_start'], params['maintenance_window_end']
                )
            )

    if params['check_conflicting_jobs']:
        if not params['controller_host'] or not params['controller_token'] or not params['template_name']:
            module.fail_json(
                msg='controller_host, controller_token, and template_name are required '
                    'when check_conflicting_jobs is true',
                neubird_preflight_failed=True,
                checks=checks,
            )
        try:
            count = get_running_job_count(
                params['controller_host'],
                params['controller_token'],
                params['template_name'],
            )
            checks['conflicting_jobs'] = 'fail' if count > 0 else 'pass'
            if count > 0:
                failures.append(
                    '{0} conflicting job(s) already running for template "{1}"'.format(
                        count, params['template_name']
                    )
                )
        except Exception as e:
            module.fail_json(
                msg='Failed to check conflicting jobs: {0}'.format(str(e)),
                neubird_preflight_failed=True,
                checks=checks,
            )

    if params['target_host']:
        reachable = check_host_reachable(params['target_host'])
        checks['target_host'] = 'pass' if reachable else 'fail'
        if not reachable:
            failures.append(
                'Target host {0} is not reachable on port 22'.format(params['target_host'])
            )

    if failures:
        module.fail_json(
            msg='Pre-flight checks failed: ' + '; '.join(failures),
            neubird_preflight_failed=True,
            checks=checks,
        )

    module.exit_json(changed=False, checks=checks)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_preflight.py -v
```

Expected: 8 PASSED.

- [ ] **Step 5: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add plugins/modules/preflight.py tests/unit/plugins/modules/test_preflight.py
git commit -m "feat: add neubird.aap.preflight module"
```

---

## Task 5: `neubird.aap.tag_safe` module

**Files:**
- Create: `plugins/modules/tag_safe.py`
- Create: `tests/unit/plugins/modules/test_tag_safe.py`

- [ ] **Step 1: Write failing unit tests `tests/unit/plugins/modules/test_tag_safe.py`**

```python
# tests/unit/plugins/modules/test_tag_safe.py
import pytest
from unittest.mock import patch, MagicMock
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson, patch_ansible

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


def test_tag_safe_template_not_found(patch_ansible):
    set_module_args(REQUIRED_ARGS)
    from ansible_collections.neubird.aap.plugins.modules import tag_safe
    with patch.object(tag_safe, 'get_template', return_value=None):
        with pytest.raises(AnsibleFailJson) as exc:
            tag_safe.main()
    assert 'not found' in exc.value.args[0]['msg']


def test_tag_safe_no_change_when_identical(patch_ansible):
    import json
    # Simulate a previously-tagged template (different timestamp, same meaningful fields)
    existing_tag = {'version': '1.0', 'tagged_at': '2020-01-01T00:00:00Z'}
    template = {
        'id': 42,
        'name': 'Rotate IAM Key',
        'extra_vars': json.dumps({'_neubird_safe': existing_tag}),
    }
    set_module_args(REQUIRED_ARGS)  # no environments/requires_approval_in/max = same as existing_tag
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_tag_safe.py -v 2>&1 | tail -10
```

Expected: `ImportError` — `tag_safe` module does not exist yet.

- [ ] **Step 3: Create `plugins/modules/tag_safe.py`**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: tag_safe
short_description: Mark an AAP job template as safe for NeuBird automated remediation
version_added: "1.0.0"
description:
  - Stores NeuBird safety metadata in a job template's extra_vars so NeuBird AI
    can discover via MCP which templates are approved for automated triggering.
  - Run once per template as an admin setup step, not inside a remediation playbook.
options:
  controller_host:
    description:
      - AAP controller base URL.
    type: str
    required: true
  controller_token:
    description:
      - AAP controller OAuth token.
    type: str
    required: true
    no_log: true
  template_name:
    description:
      - Name of the AAP job template to tag.
    type: str
    required: true
  environments:
    description:
      - Environments where NeuBird may auto-run this template.
        Omit to allow all environments.
    type: list
    elements: str
    required: false
    default: []
  requires_approval_in:
    description:
      - Environments where NeuBird must request human approval before running.
    type: list
    elements: str
    required: false
    default: []
  max_auto_runs_per_hour:
    description:
      - Maximum automated runs NeuBird may trigger per hour. Omit for no limit.
    type: int
    required: false
    default: null
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Mark template as safe for automated remediation
  neubird.aap.tag_safe:
    controller_host: "https://aap.example.com"
    controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
    template_name: "Rotate IAM Key"
    environments:
      - dev
      - staging
    requires_approval_in:
      - prod
    max_auto_runs_per_hour: 5
'''

RETURN = r'''
template_id:
  description: ID of the updated job template.
  type: int
  returned: always
  sample: 42
neubird_safe_tag:
  description: The NeuBird safety metadata written to the template extra_vars.
  type: dict
  returned: always
'''

import datetime
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


def get_template(controller_host, controller_token, template_name):
    url = '{0}/api/v2/job_templates/?name={1}'.format(
        controller_host.rstrip('/'), template_name
    )
    response = open_url(
        url,
        headers={
            'Authorization': 'Bearer {0}'.format(controller_token),
            'Content-Type': 'application/json',
        },
        method='GET',
        validate_certs=True,
    )
    data = json.loads(response.read())
    if data['count'] == 0:
        return None
    return data['results'][0]


def patch_template_extra_vars(controller_host, controller_token, template_id, extra_vars):
    url = '{0}/api/v2/job_templates/{1}/'.format(
        controller_host.rstrip('/'), template_id
    )
    payload = json.dumps({'extra_vars': json.dumps(extra_vars)}).encode('utf-8')
    response = open_url(
        url,
        data=payload,
        headers={
            'Authorization': 'Bearer {0}'.format(controller_token),
            'Content-Type': 'application/json',
        },
        method='PATCH',
        validate_certs=True,
    )
    return json.loads(response.read())


def build_safe_tag(environments, requires_approval_in, max_auto_runs_per_hour):
    tag = {
        'version': '1.0',
        'tagged_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    if environments:
        tag['environments'] = environments
    if requires_approval_in:
        tag['requires_approval_in'] = requires_approval_in
    if max_auto_runs_per_hour is not None:
        tag['max_auto_runs_per_hour'] = max_auto_runs_per_hour
    return tag


def tags_are_equal(existing_tag, new_tag):
    """Compare meaningful fields only — excludes tagged_at to ensure idempotency."""
    fields = ['version', 'environments', 'requires_approval_in', 'max_auto_runs_per_hour']
    return all(existing_tag.get(f) == new_tag.get(f) for f in fields)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            controller_host=dict(type='str', required=True),
            controller_token=dict(type='str', required=True, no_log=True),
            template_name=dict(type='str', required=True),
            environments=dict(type='list', elements='str', default=[]),
            requires_approval_in=dict(type='list', elements='str', default=[]),
            max_auto_runs_per_hour=dict(type='int', required=False, default=None),
        ),
        supports_check_mode=True,
    )

    params = module.params

    try:
        template = get_template(
            params['controller_host'],
            params['controller_token'],
            params['template_name'],
        )
    except Exception as e:
        module.fail_json(msg='Failed to fetch template: {0}'.format(str(e)))

    if template is None:
        module.fail_json(
            msg='Job template "{0}" not found'.format(params['template_name'])
        )

    existing_extra_vars = {}
    raw = template.get('extra_vars', '')
    if raw:
        try:
            existing_extra_vars = json.loads(raw)
        except (ValueError, TypeError):
            existing_extra_vars = {}

    safe_tag = build_safe_tag(
        environments=params['environments'],
        requires_approval_in=params['requires_approval_in'],
        max_auto_runs_per_hour=params['max_auto_runs_per_hour'],
    )

    existing_tag = existing_extra_vars.get('_neubird_safe', {})
    if existing_tag and tags_are_equal(existing_tag, safe_tag):
        module.exit_json(
            changed=False,
            template_id=template['id'],
            neubird_safe_tag=safe_tag,
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            template_id=template['id'],
            neubird_safe_tag=safe_tag,
        )

    existing_extra_vars['_neubird_safe'] = safe_tag

    try:
        patch_template_extra_vars(
            params['controller_host'],
            params['controller_token'],
            template['id'],
            existing_extra_vars,
        )
    except Exception as e:
        module.fail_json(msg='Failed to update template: {0}'.format(str(e)))

    module.exit_json(
        changed=True,
        template_id=template['id'],
        neubird_safe_tag=safe_tag,
    )


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_tag_safe.py -v
```

Expected: 5 PASSED.

- [ ] **Step 5: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add plugins/modules/tag_safe.py tests/unit/plugins/modules/test_tag_safe.py
git commit -m "feat: add neubird.aap.tag_safe module"
```

---

## Task 6: `neubird.aap.audit` module

**Files:**
- Create: `plugins/modules/audit.py`
- Create: `tests/unit/plugins/modules/test_audit.py`

- [ ] **Step 1: Write failing unit tests `tests/unit/plugins/modules/test_audit.py`**

```python
# tests/unit/plugins/modules/test_audit.py
import pytest
from unittest.mock import patch, MagicMock, call
from tests.unit.conftest import set_module_args, AnsibleExitJson, AnsibleFailJson, patch_ansible


def test_audit_stdout(patch_ansible, capsys):
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_audit.py -v 2>&1 | tail -10
```

Expected: `ImportError` — `audit` module does not exist yet.

- [ ] **Step 3: Create `plugins/modules/audit.py`**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: audit
short_description: Write a structured audit record for NeuBird-triggered remediation
version_added: "1.0.0"
description:
  - Writes a structured audit record after NeuBird AI triggers a remediation
    action. Supports stdout, syslog, and webhook destinations.
  - Satisfies compliance requirements for automated remediation in regulated
    environments.
options:
  action:
    description:
      - Short identifier for the action taken (e.g., iam_key_disabled).
    type: str
    required: true
  triggered_by:
    description:
      - Who or what triggered the action. Convention is neubird_ai.
    type: str
    required: true
  investigation_id:
    description:
      - NeuBird investigation ID.
    type: str
    required: false
  destination:
    description:
      - Where to write the audit record.
    type: str
    required: false
    default: stdout
    choices: ['stdout', 'syslog', 'webhook']
  webhook_url:
    description:
      - Webhook URL to POST the audit record to.
        Required when destination is webhook.
    type: str
    required: false
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Write audit record to syslog
  neubird.aap.audit:
    action: "iam_key_disabled"
    triggered_by: "neubird_ai"
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    destination: syslog

- name: Write audit record to webhook
  neubird.aap.audit:
    action: "sg_rule_removed"
    triggered_by: "neubird_ai"
    destination: webhook
    webhook_url: "https://audit.example.com/events"
'''

RETURN = r'''
audit_record:
  description: The audit record that was written.
  type: dict
  returned: always
  sample:
    schema_version: "1.0"
    timestamp: "2026-05-23T14:00:00Z"
    action: "iam_key_disabled"
    triggered_by: "neubird_ai"
    investigation_id: "inv-1234"
'''

import datetime
import json
import logging
import logging.handlers

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


def build_record(action, triggered_by, investigation_id):
    return {
        'schema_version': '1.0',
        'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'action': action,
        'triggered_by': triggered_by,
        'investigation_id': investigation_id,
    }


def write_stdout(record):
    print('NEUBIRD_AUDIT: ' + json.dumps(record))


def write_syslog(record):
    logger = logging.getLogger('neubird.aap.audit')
    if not logger.handlers:
        try:
            handler = logging.handlers.SysLogHandler(address='/dev/log')
        except (OSError, ConnectionRefusedError):
            handler = logging.handlers.SysLogHandler()
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info('NEUBIRD_AUDIT: ' + json.dumps(record))


def write_webhook(record, webhook_url):
    payload = json.dumps(record).encode('utf-8')
    open_url(
        webhook_url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
        validate_certs=True,
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True),
            triggered_by=dict(type='str', required=True),
            investigation_id=dict(type='str', required=False, default=None),
            destination=dict(
                type='str',
                required=False,
                default='stdout',
                choices=['stdout', 'syslog', 'webhook'],
            ),
            webhook_url=dict(type='str', required=False, default=None),
        ),
        required_if=[('destination', 'webhook', ['webhook_url'])],
        supports_check_mode=True,
    )

    params = module.params
    record = build_record(
        action=params['action'],
        triggered_by=params['triggered_by'],
        investigation_id=params['investigation_id'],
    )

    if module.check_mode:
        module.exit_json(changed=False, audit_record=record)

    try:
        destination = params['destination']
        if destination == 'stdout':
            write_stdout(record)
        elif destination == 'syslog':
            write_syslog(record)
        elif destination == 'webhook':
            write_webhook(record, params['webhook_url'])
    except Exception as e:
        module.fail_json(
            msg='Failed to write audit record: {0}'.format(str(e)),
            audit_record=record,
        )

    module.exit_json(changed=False, audit_record=record)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/plugins/modules/test_audit.py -v
```

Expected: 7 PASSED.

- [ ] **Step 5: Run the full unit suite to verify nothing broke**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
python3 -m pytest tests/unit/ -v
```

Expected: all tests PASSED.

- [ ] **Step 6: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add plugins/modules/audit.py tests/unit/plugins/modules/test_audit.py
git commit -m "feat: add neubird.aap.audit module"
```

---

## Task 7: Documentation files

**Files:**
- Create: `docs/report.md`, `docs/tag_safe.md`, `docs/context.md`, `docs/preflight.md`, `docs/audit.md`

- [ ] **Step 1: Create `docs/report.md`**

```markdown
# neubird.aap.report

Report remediation results to NeuBird AI.

## Synopsis

Add this module near the end of any playbook NeuBird may trigger. It surfaces structured execution results that NeuBird reads back through its MCP connection to AAP to close an investigation.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `investigation_id` | str | no | null | NeuBird investigation ID |
| `status` | str | yes | — | One of: `remediated`, `failed`, `no_change` |
| `changed_resources` | list[str] | no | `[]` | Resource identifiers that were modified |
| `detail` | dict | no | `{}` | Raw task result or structured detail |

## Return Values

| Key | Type | Description |
|---|---|---|
| `neubird_report` | dict | Structured report written to job output |

## Example

```yaml
- name: Report remediation result to NeuBird
  neubird.aap.report:
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    status: remediated
    changed_resources:
      - "sg-abc123"
    detail: "{{ task_result }}"
```
```

- [ ] **Step 2: Create `docs/tag_safe.md`**

```markdown
# neubird.aap.tag_safe

Mark an AAP job template as safe for NeuBird automated remediation.

## Synopsis

Run once per job template as an admin setup step. Stores NeuBird safety metadata in the template's `extra_vars` so NeuBird AI can discover via MCP which templates are approved for automated triggering and under what conditions.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `controller_host` | str | yes | — | AAP controller base URL |
| `controller_token` | str | yes | — | AAP OAuth token (not logged) |
| `template_name` | str | yes | — | Name of the job template to tag |
| `environments` | list[str] | no | `[]` | Environments where auto-run is approved. Omit = all. |
| `requires_approval_in` | list[str] | no | `[]` | Environments requiring human approval |
| `max_auto_runs_per_hour` | int | no | null | Rate limit for automated triggering |

## Example

```yaml
- name: Mark template as safe for automated remediation
  neubird.aap.tag_safe:
    controller_host: "https://aap.example.com"
    controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
    template_name: "Rotate IAM Key"
    environments: [dev, staging]
    requires_approval_in: [prod]
    max_auto_runs_per_hour: 5
```
```

- [ ] **Step 3: Create `docs/context.md`**

```markdown
# neubird.aap.context

Read NeuBird investigation context from AAP job variables.

## Synopsis

When NeuBird AI triggers an AAP job it passes investigation context as `_neubird_context` in the job's extra vars. This lookup plugin makes that context available inside the playbook. When the job was not triggered by NeuBird, all keys return `null`.

## Returns

| Key | Type | Description |
|---|---|---|
| `investigation_id` | str or null | NeuBird investigation identifier |
| `severity` | str or null | Severity level of the investigation |
| `affected_resource` | str or null | Resource identifier that triggered the investigation |
| `triggered_by` | str or null | Originator — `neubird_ai` when AI-triggered |

## Example

```yaml
- name: Load NeuBird investigation context
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Use context in a task
  neubird.aap.report:
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    status: remediated
```
```

- [ ] **Step 4: Create `docs/preflight.md`**

```markdown
# neubird.aap.preflight

Run pre-flight safety checks before NeuBird-triggered jobs.

## Synopsis

Place as the first task in any playbook tagged for automated remediation. Fails the play with a structured error NeuBird can parse via MCP if any check fails. Makes no changes to the system.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `check_maintenance_window` | bool | no | `false` | Fail if inside the defined maintenance window |
| `maintenance_window_start` | str | no | — | Window start in HH:MM UTC. Required if check enabled. |
| `maintenance_window_end` | str | no | — | Window end in HH:MM UTC. Required if check enabled. |
| `check_conflicting_jobs` | bool | no | `false` | Fail if same template is already running |
| `controller_host` | str | no | — | AAP URL. Required if check_conflicting_jobs enabled. |
| `controller_token` | str | no | — | AAP OAuth token. Required if check_conflicting_jobs enabled. |
| `template_name` | str | no | — | Template to check. Required if check_conflicting_jobs enabled. |
| `target_host` | str | no | — | Hostname to verify is reachable on port 22 |

## Example

```yaml
- name: Run pre-flight safety checks
  neubird.aap.preflight:
    check_maintenance_window: true
    maintenance_window_start: "02:00"
    maintenance_window_end: "04:00"
    target_host: "{{ inventory_hostname }}"
```
```

- [ ] **Step 5: Create `docs/audit.md`**

```markdown
# neubird.aap.audit

Write a structured audit record for NeuBird-triggered remediation.

## Synopsis

Writes a structured JSON audit record after a NeuBird-triggered remediation action. Supports stdout, syslog, and webhook destinations for integration with existing logging infrastructure.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `action` | str | yes | — | Short action identifier (e.g., `iam_key_disabled`) |
| `triggered_by` | str | yes | — | Who triggered the action. Convention: `neubird_ai` |
| `investigation_id` | str | no | null | NeuBird investigation ID |
| `destination` | str | no | `stdout` | One of: `stdout`, `syslog`, `webhook` |
| `webhook_url` | str | no | — | Required when destination is `webhook` |

## Example

```yaml
- name: Write audit record
  neubird.aap.audit:
    action: "iam_key_disabled"
    triggered_by: "neubird_ai"
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    destination: syslog
```
```

- [ ] **Step 6: Commit docs**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add docs/
git commit -m "docs: add per-module documentation"
```

---

## Task 8: ansible-test sanity

- [ ] **Step 1: Run sanity tests**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-test sanity --python 3.13 2>&1 | tee /tmp/sanity-output.txt
cat /tmp/sanity-output.txt
```

- [ ] **Step 2: Fix any `validate-modules` failures**

Common failures and fixes:

**"Missing DOCUMENTATION"** — ensure every module has `DOCUMENTATION`, `EXAMPLES`, `RETURN` strings.

**"DOCUMENTATION.module not found"** — ensure DOCUMENTATION YAML has `module:` key matching the filename (without `.py`). For example, `report.py` must have `module: report`.

**"RETURN is not valid YAML"** — check indentation inside the RETURN string.

**"author must be a list"** — ensure `author:` in DOCUMENTATION is a list, not a string.

After each fix, re-run:
```bash
ansible-test sanity --python 3.13 --test validate-modules
```

- [ ] **Step 3: Fix any `pylint` failures**

Common failures:

**"W0611 unused-import"** — remove any import not used in the module.

**"C0301 line-too-long"** — break lines longer than 160 chars (ansible uses 160 not 79).

After fixing:
```bash
ansible-test sanity --python 3.13 --test pylint
```

- [ ] **Step 4: Fix any `pep8` failures**

```bash
ansible-test sanity --python 3.13 --test pep8
```

Common fix: trailing whitespace, missing blank lines between functions.

- [ ] **Step 5: If a check cannot be fixed, add to `tests/sanity/ignore.txt`**

Format (only use this as a last resort):
```
plugins/modules/audit.py pylint:W0611
```

- [ ] **Step 6: Verify clean sanity run**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-test sanity --python 3.13
```

Expected: `Sanity check passed.` with no errors.

- [ ] **Step 7: Commit**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add .
git commit -m "fix: resolve ansible-test sanity failures"
```

---

## Task 9: Integration tests + galaxy-importer

- [ ] **Step 1: Create integration test for `report`**

```yaml
# tests/integration/targets/report/tasks/main.yml
---
- name: Test report module - remediated status
  neubird.aap.report:
    status: remediated
    investigation_id: "test-inv-001"
    changed_resources:
      - "test-resource-1"
  register: result

- name: Verify report structure
  assert:
    that:
      - result.changed == false
      - result.neubird_report.status == "remediated"
      - result.neubird_report.schema_version == "1.0"
      - result.neubird_report.investigation_id == "test-inv-001"
      - result.neubird_report.changed_resources == ["test-resource-1"]
      - result.neubird_report.timestamp is defined

- name: Test report module - no_change status
  neubird.aap.report:
    status: no_change
  register: result_no_change

- name: Verify no_change
  assert:
    that:
      - result_no_change.neubird_report.status == "no_change"
      - result_no_change.neubird_report.investigation_id is none
```

```
# tests/integration/targets/report/aliases
posix
```

- [ ] **Step 2: Create integration test for `audit`**

```yaml
# tests/integration/targets/audit/tasks/main.yml
---
- name: Test audit module - stdout destination
  neubird.aap.audit:
    action: "test_action"
    triggered_by: "neubird_ai"
    investigation_id: "test-inv-001"
    destination: stdout
  register: result

- name: Verify audit record structure
  assert:
    that:
      - result.changed == false
      - result.audit_record.action == "test_action"
      - result.audit_record.triggered_by == "neubird_ai"
      - result.audit_record.investigation_id == "test-inv-001"
      - result.audit_record.schema_version == "1.0"
      - result.audit_record.timestamp is defined

- name: Test audit check mode - no write occurs
  neubird.aap.audit:
    action: "test_action_check"
    triggered_by: "neubird_ai"
  check_mode: true
  register: result_check

- name: Verify check mode result
  assert:
    that:
      - result_check.changed == false
      - result_check.audit_record.action == "test_action_check"
```

```
# tests/integration/targets/audit/aliases
posix
```

- [ ] **Step 3: Create integration test for `context`**

```yaml
# tests/integration/targets/context/tasks/main.yml
---
- name: Test context lookup - no context injected
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Verify empty context graceful fallback
  assert:
    that:
      - neubird_ctx.investigation_id is none
      - neubird_ctx.severity is none
      - neubird_ctx.affected_resource is none
      - neubird_ctx.triggered_by is none

- name: Test context lookup - with injected context
  set_fact:
    _neubird_context:
      investigation_id: "inv-test-001"
      severity: "high"
      affected_resource: "sg-abc"
      triggered_by: "neubird_ai"

- name: Read injected context
  set_fact:
    neubird_ctx_injected: "{{ lookup('neubird.aap.context') }}"

- name: Verify injected context is returned
  assert:
    that:
      - neubird_ctx_injected.investigation_id == "inv-test-001"
      - neubird_ctx_injected.severity == "high"
      - neubird_ctx_injected.triggered_by == "neubird_ai"
```

```
# tests/integration/targets/context/aliases
posix
```

- [ ] **Step 4: Run integration tests**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-test integration report audit context --python 3.13 -v
```

Expected: all integration tests pass.

- [ ] **Step 5: Run ansible-lint**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-lint
```

Fix any failures. Common ones:
- `yaml[truthy]`: use `true`/`false` not `yes`/`no` in YAML
- `name[casing]`: task names should start with uppercase
- `no-free-form`: use dict syntax not free-form for module args

Re-run until clean.

- [ ] **Step 6: Build the collection tarball**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
ansible-galaxy collection build --output-path /tmp/
```

Expected: `/tmp/neubird-aap-1.0.0.tar.gz` created.

- [ ] **Step 7: Run galaxy-importer**

```bash
python3 -m galaxy_importer.main /tmp/neubird-aap-1.0.0.tar.gz
```

Expected: `INFO: ...process complete` with no errors. Any warnings should be reviewed — some are blocking for certification.

- [ ] **Step 8: Final commit and tag**

```bash
cd /Users/alee/Desktop/Development/ansible_collections/neubird/aap
git add tests/integration/ tests/sanity/
git commit -m "test: add integration tests and sanity config"
git tag v1.0.0
```

---

## Pre-Certification Checklist

Before submitting to Red Hat, verify:

- [ ] `ansible-test sanity --python 3.13` passes clean
- [ ] `ansible-test units --python 3.13` passes clean
- [ ] `ansible-test integration report audit context` passes clean
- [ ] `ansible-lint` passes clean
- [ ] `galaxy-importer` passes with no errors
- [ ] `galaxy.yml` has valid `repository` URL pointing to a public GitHub repo
- [ ] `README.md` covers installation and all five modules/plugins with examples
- [ ] Email `ansiblepartners@redhat.com` to request the `neubird` namespace on Automation Hub
