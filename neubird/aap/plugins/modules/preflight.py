#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
  - NeuBird (@neubird-ai)
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
from ansible.module_utils.six.moves.urllib.parse import quote


def check_maintenance_window(start_str, end_str, current_time=None):
    if current_time is None:
        current_time = datetime.datetime.now(datetime.timezone.utc).time()
    start = datetime.time(*[int(x) for x in start_str.split(':')])
    end = datetime.time(*[int(x) for x in end_str.split(':')])
    if start <= end:
        return start <= current_time <= end
    return current_time >= start or current_time <= end


def check_host_reachable(hostname, port=22, timeout=5):
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False


def get_running_job_count(controller_host, controller_token, template_name):
    url = '{0}/api/controller/v2/jobs/?status=running&job_template__name={1}'.format(
        controller_host.rstrip('/'), quote(template_name, safe='')
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
