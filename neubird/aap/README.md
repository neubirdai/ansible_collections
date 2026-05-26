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
