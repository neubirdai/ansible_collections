#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: investigate
short_description: Trigger a NeuBird AI investigation from an Ansible playbook
version_added: "1.1.0"
description:
  - Authenticates with NeuBird, looks up the named project, and fires an investigation
    with the supplied context and prompt.
  - By default returns immediately with the session UUID so the playbook can continue
    and retrieve results later with investigation_result.
  - Set wait=true to block until the investigation completes and return findings inline.
options:
  neubird_url:
    description: Base URL of the NeuBird instance (e.g. https://your-tenant.neubird.ai).
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
  neubird_project:
    description: Name of the NeuBird project to investigate in (exact match).
    type: str
    required: true
  context:
    description:
      - Data for the investigation. Accepts a dict (serialized to JSON) or a string.
        Typically the registered output of a prior playbook task.
    type: raw
    required: true
  prompt_text:
    description: Investigation directive prepended to the context.
    type: str
    required: false
    default: "Investigate the following context"
  wait:
    description: If true, block until the investigation completes and return findings.
    type: bool
    required: false
    default: false
  wait_timeout:
    description: Maximum seconds to wait when wait=true.
    type: int
    required: false
    default: 300
author:
  - NeuBird AI (@neubird-ai)
'''

EXAMPLES = r'''
- name: Trigger EKS investigation (fire-and-forget)
  neubird.aap.investigate:
    neubird_url: "https://your-tenant.neubird.ai"
    neubird_username: "{{ neubird_user }}"
    neubird_password: "{{ neubird_pass }}"
    neubird_project: "Red Hat"
    context: "{{ eks_deploy_result }}"
    prompt_text: "Verify this EKS deployment is healthy"
  register: investigation

- name: Trigger and wait for result inline
  neubird.aap.investigate:
    neubird_url: "https://your-tenant.neubird.ai"
    neubird_username: "{{ neubird_user }}"
    neubird_password: "{{ neubird_pass }}"
    neubird_project: "Red Hat"
    context: "{{ deployment_facts }}"
    wait: true
    wait_timeout: 600
  register: result
'''

RETURN = r'''
session_uuid:
  description: NeuBird session UUID. Pass to investigation_result to retrieve findings later.
  type: str
  returned: always
  sample: "6a1dec79..."
status:
  description: Investigation status at time of return.
  type: str
  returned: always
  sample: "INVESTIGATION_STATUS_IN_PROGRESS"
confidence:
  description: NeuBird confidence score (0-100). Only present when wait=true and completed.
  type: float
  returned: when wait=true and investigation completed
  sample: 88.0
elapsed_seconds:
  description: Investigation duration in seconds. Only present when wait=true and completed.
  type: int
  returned: when wait=true and investigation completed
  sample: 204
summary_sections:
  description: List of investigation findings sections with title and markdown content.
  type: list
  returned: when wait=true and investigation completed
  sample:
    - title: "Executive Summary"
      content: "Cluster is healthy."
'''

import datetime
import json
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.neubird.aap.plugins.module_utils import neubird_client


def build_prompt(context, prompt_text):
    if isinstance(context, dict):
        return '{0}:\n\n{1}'.format(prompt_text, json.dumps(context, indent=2))
    return '{0}:\n\n{1}'.format(prompt_text, context)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            neubird_url=dict(type='str', required=True),
            neubird_username=dict(type='str', required=True),
            neubird_password=dict(type='str', required=True, no_log=True),
            neubird_project=dict(type='str', required=True),
            context=dict(type='raw', required=True),
            prompt_text=dict(type='str', default='Investigate the following context'),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
        ),
        supports_check_mode=False,
    )

    p = module.params

    try:
        token = neubird_client.login(p['neubird_url'], p['neubird_username'], p['neubird_password'])
    except Exception as e:
        module.fail_json(msg='Authentication failed: {0}'.format(str(e)))

    try:
        project_uuid = neubird_client.get_project_uuid(p['neubird_url'], token, p['neubird_project'])
    except Exception as e:
        module.fail_json(msg='Failed to look up project: {0}'.format(str(e)))

    if project_uuid is None:
        module.fail_json(msg="Project '{0}' not found".format(p['neubird_project']))

    prompt = build_prompt(p['context'], p['prompt_text'])
    pre_trigger_time = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        if p['wait']:
            neubird_client.wait_for_investigation(
                p['neubird_url'], token, project_uuid, prompt,
                timeout=p['wait_timeout'] + 60,
            )
        else:
            neubird_client.trigger_investigation(p['neubird_url'], token, project_uuid, prompt)
    except Exception as e:
        module.fail_json(msg='Failed to trigger investigation: {0}'.format(str(e)))

    time.sleep(1)

    try:
        session = neubird_client.get_session_by_time(
            p['neubird_url'], token, project_uuid, pre_trigger_time
        )
    except Exception as e:
        module.fail_json(msg='Failed to retrieve session: {0}'.format(str(e)))

    if session is None:
        module.fail_json(msg='Investigation started but session UUID could not be retrieved')

    session_uuid = session['session_uuid']
    result = dict(
        changed=False,
        session_uuid=session_uuid,
        status=session.get('investigation_status', 'INVESTIGATION_STATUS_IN_PROGRESS'),
    )

    if p['wait'] and session.get('investigation_status') in (
        'INVESTIGATION_STATUS_COMPLETED', 'INVESTIGATION_STATUS_STOPPED'
    ):
        try:
            meta_resp = neubird_client.get_session_metadata(p['neubird_url'], token, session_uuid)
            meta = meta_resp.get('session_metadata', {})
            result['confidence'] = meta.get('confidence')
            result['elapsed_seconds'] = int(float(meta.get('elapsed_time_seconds', 0)))
            summary = neubird_client.get_session_summary(p['neubird_url'], token, session_uuid)
            result['summary_sections'] = summary.get('sections', [])
        except Exception as e:
            module.fail_json(msg='Failed to retrieve investigation results: {0}'.format(str(e)))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
