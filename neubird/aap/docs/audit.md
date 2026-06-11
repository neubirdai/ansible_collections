# neubird.aap.audit

Write a structured audit record for NeuBird-triggered remediation.

## Synopsis

Writes a structured JSON audit record after a NeuBird-triggered remediation action. Supports stdout, syslog, and webhook destinations for integration with existing logging infrastructure.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `action` | str | yes | — | Short action identifier (e.g., `iam_key_disabled`) |
| `triggered_by` | str | yes | — | Who triggered the action. Convention: `neubird_ai` |
| `investigation_id` | str | no | null | NeuBird investigation ID |
| `destination` | str | no | `stdout` | One of: `stdout`, `syslog`, `webhook` |
| `webhook_url` | str | no | — | Required when destination is `webhook` |

## Example

```yaml
- name: Write audit record
  neubird.aap.audit:
    action: "iam_key_disabled"
    triggered_by: "neubird_ai"
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    destination: syslog
```
