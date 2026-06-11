# neubird.aap.preflight

Run pre-flight safety checks before NeuBird-triggered jobs.

## Synopsis

Place as the first task in any playbook tagged for automated remediation. Fails the play with a structured error NeuBird can parse via MCP if any check fails. Makes no changes to the system.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `check_maintenance_window` | bool | no | `false` | Fail if inside the defined maintenance window |
| `maintenance_window_start` | str | no | — | Window start in HH:MM UTC. Required if check enabled. |
| `maintenance_window_end` | str | no | — | Window end in HH:MM UTC. Required if check enabled. |
| `check_conflicting_jobs` | bool | no | `false` | Fail if same template is already running |
| `controller_host` | str | no | — | AAP URL. Required if check_conflicting_jobs enabled. |
| `controller_token` | str | no | — | AAP OAuth token. Required if check_conflicting_jobs enabled. |
| `template_name` | str | no | — | Template to check. Required if check_conflicting_jobs enabled. |
| `target_host` | str | no | — | Hostname to verify is reachable on port 22 |

## Example

```yaml
- name: Run pre-flight safety checks
  neubird.aap.preflight:
    check_maintenance_window: true
    maintenance_window_start: "02:00"
    maintenance_window_end: "04:00"
    target_host: "{{ inventory_hostname }}"
```
