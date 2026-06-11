# neubird.aap.tag_safe

Mark an AAP job template as safe for NeuBird automated remediation.

## Synopsis

Run once per job template as an admin setup step. Stores NeuBird safety metadata in the template's `extra_vars` so NeuBird AI can discover via MCP which templates are approved for automated triggering and under what conditions.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `controller_host` | str | yes | — | AAP controller base URL |
| `controller_token` | str | yes | — | AAP OAuth token (not logged) |
| `template_name` | str | yes | — | Name of the job template to tag |
| `environments` | list[str] | no | `[]` | Environments where auto-run is approved. Omit = all. |
| `requires_approval_in` | list[str] | no | `[]` | Environments requiring human approval |
| `max_auto_runs_per_hour` | int | no | null | Rate limit for automated triggering |

## Example

```yaml
- name: Mark template as safe for automated remediation
  neubird.aap.tag_safe:
    controller_host: "https://aap.example.com"
    controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
    template_name: "Rotate IAM Key"
    environments: [dev, staging]
    requires_approval_in: [prod]
    max_auto_runs_per_hour: 5
```
