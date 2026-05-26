# Design: `neubird.aap` Ansible Collection v1.0

**Date:** 2026-05-23
**Status:** Approved
**Author:** NeuBird AI

---

## Purpose & Positioning

`neubird.aap` is a Red Hat certified Ansible collection that acts as the intelligence gateway between an organization's existing AAP job templates and NeuBird AI. It does not provide remediation playbooks — customers own those. Instead, it provides the modules that make any playbook AI-aware: reporting results, declaring safety, carrying investigation context, gating execution, and logging actions.

NeuBird AI is the orchestrator. It connects to AAP via AAP's MCP server, discovers job templates, determines which templates to run based on active investigations, and triggers them automatically. `neubird.aap` is the collection that makes that loop complete — giving NeuBird structured data to act on and giving admins the governance controls to stay in control.

### What it is not

- Not a library of remediation playbooks (customers bring their own)
- Not a cloud provider integration (no dependency on `amazon.aws`, `kubernetes.core`, or any other collection)
- Not an EDA integration (planned for v2)

---

## Certification Target

- **Track:** Certified Content Collection (Python modules)
- **Namespace:** `neubird` (to be requested from Red Hat via `ansiblepartners@redhat.com`)
- **Collection name:** `aap`
- **Full name:** `neubird.aap`
- **License:** Apache-2.0
- **Ansible-core support:** 2.16 and 2.17 (minimum two versions, tied to supported AAP releases)
- **Dependencies:** None (intentionally empty — stands alone)

---

## Collection Structure

```
neubird/aap/
├── galaxy.yml
├── README.md
├── meta/
│   └── runtime.yml
├── plugins/
│   └── modules/
│       ├── report.py
│       ├── tag_safe.py
│       ├── preflight.py
│       └── audit.py
│   └── lookup/
│       └── context.py
├── docs/
│   ├── report.md
│   ├── tag_safe.md
│   ├── context.md
│   ├── preflight.md
│   └── audit.md
└── tests/
    ├── sanity/
    └── integration/
```

### `galaxy.yml` key fields

```yaml
namespace: neubird
name: aap
version: 1.0.0
license:
  - Apache-2.0
description: >
  Intelligence gateway between Ansible Automation Platform and NeuBird AI.
  Makes any AAP job template AI-aware with reporting, safety tagging,
  context injection, pre-flight gating, and audit logging.
repository: https://github.com/neubird-ai/ansible-collection
dependencies: {}
tags:
  - ai
  - automation
  - remediation
  - monitoring
  - neubird
```

---

## Module Designs

### 1. `neubird.aap.report`

**Purpose:** Surface structured job execution results in a format NeuBird can read back through its MCP connection to AAP, closing the investigation loop.

**When to use:** Added as a task near the end of any playbook that NeuBird may trigger. Works on any job — not just NeuBird-triggered ones.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `investigation_id` | string | no | NeuBird investigation ID. If omitted, report is standalone. |
| `status` | string | yes | One of: `remediated`, `failed`, `no_change` |
| `changed_resources` | list | no | List of resource identifiers that were modified |
| `detail` | dict | no | Raw task result or any structured detail to pass through |

**Output:** Writes a structured JSON artifact to the job's output that NeuBird reads via MCP.

```yaml
- name: Report remediation result to NeuBird
  neubird.aap.report:
    investigation_id: "{{ neubird_investigation_id | default(omit) }}"
    status: "remediated"
    changed_resources:
      - "{{ affected_resource }}"
    detail: "{{ remediation_result }}"
```

---

### 2. `neubird.aap.tag_safe`

**Purpose:** Allow admins to mark a job template as approved for automated remediation by NeuBird. NeuBird discovers tagged templates via MCP and knows it can trigger them without human approval — within the declared scope.

**When to use:** Run once by an admin per job template. Not part of the remediation playbook itself.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `template_name` | string | yes | Name of the AAP job template to tag |
| `environments` | list | no | Environments where auto-run is approved. Omit = all. |
| `requires_approval_in` | list | no | Environments requiring human approval before NeuBird runs |
| `max_auto_runs_per_hour` | int | no | Rate limit for automated triggering. Default: unlimited. |

```yaml
- name: Mark template as safe for automated remediation
  neubird.aap.tag_safe:
    template_name: "Rotate IAM Key"
    environments:
      - dev
      - staging
    requires_approval_in:
      - prod
    max_auto_runs_per_hour: 5
```

---

### 3. `neubird.aap.context` (lookup plugin)

**Purpose:** When NeuBird triggers a job, it passes investigation context at launch time. This lookup plugin makes that context available as variables inside the running playbook — so tasks can log, branch, or report against the specific investigation that triggered them.

**When to use:** At the top of any playbook that may be NeuBird-triggered, to pull in investigation context.

**Returns:** Dict with `investigation_id`, `severity`, `affected_resource`, `triggered_by`.

```yaml
- name: Load NeuBird investigation context
  set_fact:
    neubird_ctx: "{{ lookup('neubird.aap.context') }}"

- name: Use context downstream
  debug:
    msg: "Remediating {{ neubird_ctx.affected_resource }} for investigation {{ neubird_ctx.investigation_id }}"
```

**Behavior when not triggered by NeuBird:** Returns an empty dict with all keys set to `null`. Playbooks degrade gracefully.

---

### 4. `neubird.aap.preflight`

**Purpose:** Before NeuBird auto-runs a job, validate that conditions are safe. Returns a structured pass/fail that NeuBird reads via MCP before deciding to proceed. Gives admins a programmatic veto over automated execution.

**When to use:** As the first task in any playbook tagged for automated remediation.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `check_maintenance_window` | bool | no | Fail if inside a defined maintenance window. Default: `false` |
| `check_conflicting_jobs` | bool | no | Fail if another job targeting same resources is running. Default: `false` |
| `target_host` | string | no | Hostname to verify is reachable before proceeding |

**Behavior on failure:** Fails the play with a structured error message NeuBird can parse. Does not make any changes.

```yaml
- name: Run pre-flight safety checks
  neubird.aap.preflight:
    check_maintenance_window: true
    check_conflicting_jobs: true
    target_host: "{{ inventory_hostname | default(omit) }}"
```

---

### 5. `neubird.aap.audit`

**Purpose:** Write a structured audit record for every NeuBird-triggered remediation action. Satisfies compliance requirements for automated remediation in regulated environments. Plugs into existing logging infrastructure.

**When to use:** After significant state-changing tasks in any NeuBird-triggered playbook.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `action` | string | yes | Short identifier for the action taken (e.g., `iam_key_disabled`) |
| `triggered_by` | string | yes | Who/what triggered this. Convention: `neubird_ai` |
| `investigation_id` | string | no | NeuBird investigation ID |
| `destination` | string | no | One of: `stdout` (default), `syslog`, `webhook` |
| `webhook_url` | string | no | Required when `destination: webhook` |

```yaml
- name: Write audit record
  neubird.aap.audit:
    action: "iam_key_disabled"
    triggered_by: "neubird_ai"
    investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
    destination: syslog
```

---

## Testing Requirements (for Certification)

- **Sanity:** All modules pass `ansible-test sanity` with ansible-core 2.16
- **Lint:** All content passes `ansible-lint` (current version)
- **Integration tests:** Each module has at least one integration test with a mock AAP/MCP endpoint
- **galaxy-importer:** Collection passes `galaxy-importer` validation before submission

---

## Certification Submission Checklist

- [ ] Request `neubird` namespace from Red Hat (`ansiblepartners@redhat.com`)
- [ ] Source code publicly hosted on GitHub
- [ ] GitHub repository URL set in `galaxy.yml`
- [ ] All sanity, lint, and integration tests passing
- [ ] README covers installation, each module with examples, and supported AAP versions
- [ ] `meta/runtime.yml` declares minimum ansible-core version (2.16)
- [ ] Changelog present (`CHANGELOG.rst`)

---

## Out of Scope (v1)

- EDA (Event-Driven Ansible) integration — planned for v2
- Azure or GCP-specific modules
- OpenShift-specific modules
- Multi-tenant NeuBird support
- Approval workflow UI integration
