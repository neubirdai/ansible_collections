#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: report
short_description: Report remediation results to NeuBird
version_added: "1.0.0"
description:
  - Surfaces structured job execution results in a format NeuBird can read
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
  - NeuBird (@neubird-ai)
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
        'timestamp': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
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
