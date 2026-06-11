# neubird.aap

Intelligence gateway between Ansible Automation Platform and NeuBird AI.
Makes any existing AAP job template AI-aware by adding structured context
injection, pre-flight safety gating, result reporting, audit logging, and
safety tagging — with no changes to your existing playbooks.

## Requirements

- ansible-core >= 2.16.0
- Python >= 3.9
- Ansible Automation Platform >= 2.4

## Installation

Install from Ansible automation hub:

```bash
ansible-galaxy collection install neubird.aap
```

Or pin to a specific version:

```bash
ansible-galaxy collection install neubird.aap==1.1.0
```

## Modules

| Module | Description |
|---|---|
| `neubird.aap.report` | Report remediation results to NeuBird AI |
| `neubird.aap.tag_safe` | Mark a job template as safe for automated remediation |
| `neubird.aap.preflight` | Run pre-flight safety checks before automated job execution |
| `neubird.aap.audit` | Write structured audit records for compliance |
| `neubird.aap.investigate` | Trigger a NeuBird AI investigation from an Ansible playbook |
| `neubird.aap.investigation_result` | Retrieve the status and findings of a NeuBird investigation |

## Lookup Plugins

| Plugin | Description |
|---|---|
| `neubird.aap.context` | Read NeuBird investigation context from AAP job variables |

## Usage

Load investigation context at the start of a playbook, run pre-flight
checks, perform your remediation tasks, then report the result back:

```yaml
- name: Load NeuBird investigation context
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Pre-flight safety checks
  neubird.aap.preflight:
    check_maintenance_window: true
    maintenance_window_start: "02:00"
    maintenance_window_end: "04:00"

- name: Report result to NeuBird
  neubird.aap.report:
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    status: remediated
    changed_resources:
      - "{{ neubird_ctx.affected_resource }}"
```

All components degrade gracefully when a job is run manually rather than
triggered by NeuBird AI.

## Support

For bug reports and feature requests, open an issue on the
[GitHub issue tracker](https://github.com/neubird-ai/ansible-collection/issues).

For customers with an active Red Hat Ansible Automation Platform subscription,
support for this collection is available through the standard Red Hat support
process. NeuBird AI co-supports this collection in accordance with the Red Hat
Ansible certification program.

## Changelog

See [CHANGELOG.rst](https://github.com/neubird-ai/ansible-collection/blob/main/CHANGELOG.rst)
for the full release history and version notes.

## License

Apache-2.0. See [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) for the
full license text.
