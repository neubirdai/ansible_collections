# neubird.aap.report

Report remediation results to NeuBird.

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
