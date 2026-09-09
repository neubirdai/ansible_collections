# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
name: context
short_description: Read NeuBird investigation context from AAP job variables
version_added: "1.0.0"
description:
  - Returns the NeuBird investigation context injected by NeuBird when
    triggering an AAP job. Falls back gracefully when the job was not
    triggered by NeuBird (all keys are null).
author:
  - NeuBird (@neubird-ai)
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
