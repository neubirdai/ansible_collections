#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
        'timestamp': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'action': action,
        'triggered_by': triggered_by,
        'investigation_id': investigation_id,
    }


def write_stdout(record):
    import sys
    sys.stdout.write('NEUBIRD_AUDIT: ' + json.dumps(record) + '\n')


def write_syslog(record):
    logger = logging.getLogger('neubird.aap.audit')
    if not logger.handlers:
        try:
            handler = logging.handlers.SysLogHandler(address='/dev/log')
        except (OSError, ConnectionRefusedError):
            handler = logging.handlers.SysLogHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    logger.info('NEUBIRD_AUDIT: %s', json.dumps(record))


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

    destination = params['destination']
    if destination == 'stdout':
        write_stdout(record)
    elif destination == 'syslog':
        write_syslog(record)
    elif destination == 'webhook':
        write_webhook(record, params['webhook_url'])

    module.exit_json(changed=False, audit_record=record)


if __name__ == '__main__':
    main()
