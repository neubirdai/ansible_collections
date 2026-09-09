#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: investigation_result
short_description: Retrieve the status and findings of a NeuBird investigation
version_added: "1.1.0"
description:
  - Fetches the current status and, when complete, the full findings for a NeuBird
    session UUID returned by the investigate module.
  - Safe to call repeatedly in an until loop to poll for completion.
options:
  neubird_url:
    description: Base URL of the NeuBird instance.
    type: str
    required: true
  neubird_username:
    description: NeuBird account email address.
    type: str
    required: true
  neubird_password:
    description: NeuBird account password.
    type: str
    required: true
  session_uuid:
    description: Session UUID returned by a prior investigate task.
    type: str
    required: true
author:
  - NeuBird (@neubird-ai)
'''

EXAMPLES = r'''
- name: Poll until investigation completes
  neubird.aap.investigation_result:
    neubird_url: "https://your-tenant.neubird.ai"
    neubird_username: "{{ neubird_user }}"
    neubird_password: "{{ neubird_pass }}"
    session_uuid: "{{ investigation.session_uuid }}"
  register: result
  until: result.status == "INVESTIGATION_STATUS_COMPLETED"
  retries: 30
  delay: 30
'''

RETURN = r'''
session_uuid:
  description: The session UUID queried.
  type: str
  returned: always
  sample: "6a1dec79..."
status:
  description: Current investigation status.
  type: str
  returned: always
  sample: "INVESTIGATION_STATUS_COMPLETED"
confidence:
  description: NeuBird confidence score (0-100).
  type: float
  returned: always
  sample: 88.0
elapsed_seconds:
  description: Investigation duration in seconds.
  type: int
  returned: always
  sample: 204
steps:
  description: Number of investigation steps taken.
  type: int
  returned: always
  sample: 12
total_actions:
  description: Total tool actions executed during investigation.
  type: int
  returned: always
  sample: 35
summary_sections:
  description: Investigation findings as a list of titled markdown sections.
  type: list
  returned: when status is COMPLETED or STOPPED
  sample:
    - title: "Executive Summary"
      content: "Cluster is healthy."
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.neubird.aap.plugins.module_utils import neubird_client

_TERMINAL_STATUSES = ('INVESTIGATION_STATUS_COMPLETED', 'INVESTIGATION_STATUS_STOPPED')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            neubird_url=dict(type='str', required=True),
            neubird_username=dict(type='str', required=True),
            neubird_password=dict(type='str', required=True, no_log=True),
            session_uuid=dict(type='str', required=True),
        ),
        supports_check_mode=False,
    )

    p = module.params

    try:
        token = neubird_client.login(p['neubird_url'], p['neubird_username'], p['neubird_password'])
    except Exception as e:
        module.fail_json(msg='Authentication failed: {0}'.format(str(e)))

    try:
        meta_resp = neubird_client.get_session_metadata(p['neubird_url'], token, p['session_uuid'])
    except Exception as e:
        module.fail_json(msg='Failed to retrieve session metadata: {0}'.format(str(e)))

    meta = meta_resp.get('session_metadata', {})
    status = meta.get('investigation_status', 'INVESTIGATION_STATUS_UNKNOWN')

    result = dict(
        changed=False,
        session_uuid=p['session_uuid'],
        status=status,
        confidence=meta.get('confidence'),
        elapsed_seconds=int(float(meta.get('elapsed_time_seconds', 0))),
        steps=meta.get('steps', 0),
        total_actions=meta.get('total_actions', 0),
    )

    if status in _TERMINAL_STATUSES:
        try:
            summary = neubird_client.get_session_summary(p['neubird_url'], token, p['session_uuid'])
            result['summary_sections'] = summary.get('sections', [])
        except Exception as e:
            module.fail_json(msg='Failed to retrieve investigation summary: {0}'.format(str(e)))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
