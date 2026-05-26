#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
    response.read()


def build_safe_tag(environments, requires_approval_in, max_auto_runs_per_hour):
    tag = {
        'version': '1.0',
        'tagged_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    if environments:
        tag['environments'] = environments
    if requires_approval_in:
        tag['requires_approval_in'] = requires_approval_in
    if max_auto_runs_per_hour is not None:
        tag['max_auto_runs_per_hour'] = max_auto_runs_per_hour
    return tag


def tags_are_equal(existing_tag, new_tag):
    # tagged_at is excluded — timestamps differ on every run and must not trigger changes
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
