.. _ansible_collections.neubird.aap.docsite.guide_audit:

Writing Audit Records
======================

``neubird.aap.audit`` writes a structured JSON audit record after a NeuBird-triggered
remediation action. It is designed to satisfy compliance requirements in regulated
environments where automated changes must be logged to an external system.

Audit Record Schema
-------------------

Every record includes:

``schema_version``
    Always ``1.0`` in this collection version.

``timestamp``
    UTC ISO 8601 timestamp of when the audit record was written.

``action``
    Short identifier describing the action taken. Use a consistent naming convention
    across your playbooks. Examples: ``iam_key_disabled``, ``sg_rule_removed``,
    ``instance_stopped``.

``triggered_by``
    Who or what triggered the action. Convention is ``neubird_ai`` for AI-triggered
    jobs. Use ``manual`` or the operator's name for human-triggered runs.

``investigation_id``
    NeuBird investigation identifier. ``null`` on manual runs.

Destinations
------------

stdout (default)
~~~~~~~~~~~~~~~~

Writes the record to job standard output as a ``NEUBIRD_AUDIT:`` prefixed JSON line.
Captured by AAP's job output and visible in the job log.

.. code-block:: yaml

    - name: Write audit record
      neubird.aap.audit:
        action: "iam_key_disabled"
        triggered_by: "neubird_ai"

syslog
~~~~~~

Writes the record to the system syslog (``/dev/log`` on Linux, UDP 514 fallback).
Use this for integration with log aggregators that consume syslog (Splunk, ELK,
Datadog, etc.).

.. code-block:: yaml

    - name: Write audit record to syslog
      neubird.aap.audit:
        action: "iam_key_disabled"
        triggered_by: "{{ neubird_ctx.triggered_by | default('manual') }}"
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        destination: syslog

webhook
~~~~~~~

POSTs the record as JSON to a webhook URL. Use this for real-time integration with
SIEM, ticketing systems, or compliance platforms.

.. code-block:: yaml

    - name: Write audit record to webhook
      neubird.aap.audit:
        action: "sg_rule_removed"
        triggered_by: "{{ neubird_ctx.triggered_by | default('manual') }}"
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        destination: webhook
        webhook_url: "https://audit.example.com/events"

``webhook_url`` is required when ``destination`` is ``webhook``. The record is sent
as a ``Content-Type: application/json`` POST body.

Check Mode
----------

In check mode, ``neubird.aap.audit`` builds the audit record but does not write it
to any destination. The record is returned in the task result so you can inspect
what would be written:

.. code-block:: yaml

    - name: Audit record dry run
      neubird.aap.audit:
        action: "iam_key_disabled"
        triggered_by: "neubird_ai"
        destination: syslog
      check_mode: true
      register: audit_dry_run

    - name: Show what would be written
      debug:
        var: audit_dry_run.audit_record

Compliance Pattern
------------------

For regulated environments, combine ``neubird.aap.audit`` with ``neubird.aap.report``
at the end of every remediation playbook:

.. code-block:: yaml

    # Compliance record — goes to your log aggregator
    - name: Write compliance audit record
      neubird.aap.audit:
        action: "{{ audit_action }}"
        triggered_by: "{{ neubird_ctx.triggered_by | default('manual') }}"
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        destination: syslog

    # Operational record — closes the loop in NeuBird AI
    - name: Report result to NeuBird
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: remediated
        changed_resources: "{{ changed_resource_list }}"
