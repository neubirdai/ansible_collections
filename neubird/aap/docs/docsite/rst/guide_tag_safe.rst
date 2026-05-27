.. _ansible_collections.neubird.aap.docsite.guide_tag_safe:

Tagging Job Templates as Safe
==============================

``neubird.aap.tag_safe`` is an **administrator setup step**, not a remediation task.
Run it once per job template to declare that NeuBird AI is permitted to trigger it
automatically.

How It Works
------------

The module writes a ``_neubird_safe`` key into the job template's ``extra_vars`` via
the AAP REST API. NeuBird AI reads this key through its MCP connection to discover
which templates are approved, under what conditions, and at what rate.

.. code-block:: json

    {
      "_neubird_safe": {
        "version": "1.0",
        "environments": ["dev", "staging"],
        "requires_approval_in": ["prod"],
        "max_auto_runs_per_hour": 10,
        "tagged_at": "2026-05-23T14:00:00Z"
      }
    }

The module is idempotent. Re-running it with the same parameters makes no change.
``tagged_at`` is excluded from the idempotency comparison so timestamps never trigger
spurious changes.

Parameters
----------

``controller_host`` (required)
    Base URL of the AAP controller. Example: ``https://aap.example.com``

``controller_token`` (required)
    AAP OAuth token. Never logged.

``template_name`` (required)
    Exact name of the job template to tag as it appears in the AAP UI.

``environments`` (optional, default: ``[]``)
    List of environment names where NeuBird may auto-run this template. An empty
    list means all environments are permitted.

``requires_approval_in`` (optional, default: ``[]``)
    Environments where NeuBird must pause and request human approval before
    triggering the template.

``max_auto_runs_per_hour`` (optional, default: no limit)
    Rate limit for automated triggering. NeuBird enforces this client-side.

Examples
--------

**Permit automated runs in dev and staging, require approval in prod:**

.. code-block:: yaml

    - name: Tag remediation template
      neubird.aap.tag_safe:
        controller_host: "https://aap.example.com"
        controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
        template_name: "Rotate IAM Key"
        environments:
          - dev
          - staging
        requires_approval_in:
          - prod
        max_auto_runs_per_hour: 10

**Permit automated runs in all environments with no rate limit:**

.. code-block:: yaml

    - name: Tag template for all environments
      neubird.aap.tag_safe:
        controller_host: "https://aap.example.com"
        controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
        template_name: "Restart Application Service"

**Verify with check mode before committing:**

.. code-block:: yaml

    - name: Dry-run tag update
      neubird.aap.tag_safe:
        controller_host: "https://aap.example.com"
        controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
        template_name: "Rotate IAM Key"
        max_auto_runs_per_hour: 5
      check_mode: true

Security Notes
--------------

- ``controller_token`` is marked ``no_log`` and never appears in job output or logs.
- Tagging does not grant NeuBird any additional AAP permissions. NeuBird must still
  authenticate separately to trigger jobs.
- The ``_neubird_safe`` key is advisory metadata; it does not enforce security controls
  at the AAP level.
