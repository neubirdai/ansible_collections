# neubird.aap.context

Read NeuBird investigation context from AAP job variables.

## Synopsis

When NeuBird triggers an AAP job it passes investigation context as `_neubird_context` in the job's extra vars. This lookup plugin makes that context available inside the playbook. When the job was not triggered by NeuBird, all keys return `null`.

## Returns

| Key | Type | Description |
|---|---|---|
| `investigation_id` | str or null | NeuBird investigation identifier |
| `severity` | str or null | Severity level of the investigation |
| `affected_resource` | str or null | Resource identifier that triggered the investigation |
| `triggered_by` | str or null | Originator — `neubird_ai` when AI-triggered |

## Example

```yaml
- name: Load NeuBird investigation context
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Use context in a task
  neubird.aap.report:
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    status: remediated
```
