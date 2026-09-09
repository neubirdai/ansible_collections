.. _ansible_collections.neubird.aap.docsite.guide_report:

Reporting Results to NeuBird
=============================

``neubird.aap.report`` writes a structured result record at the end of a playbook.
NeuBird reads this record through its MCP connection to AAP to close the
investigation loop — marking the investigation as resolved, failed, or unchanged.

Place ``neubird.aap.report`` as the **last task** in any playbook NeuBird may trigger.

Report Schema
-------------

Every report includes:

``schema_version``
    Always ``1.0`` in this collection version.

``investigation_id``
    The NeuBird investigation identifier passed in via context. ``null`` on manual runs.

``status``
    One of ``remediated``, ``failed``, or ``no_change``.

``changed_resources``
    List of resource identifiers that were modified. Empty list if nothing changed.

``detail``
    Arbitrary dict for passing raw task results or structured diagnostic data back
    to NeuBird.

``timestamp``
    UTC ISO 8601 timestamp of when the report was generated.

Status Values
-------------

``remediated``
    The issue was successfully resolved. Changed resources should be listed.

``failed``
    The remediation was attempted but did not succeed. Include diagnostic detail.

``no_change``
    The resource was already in the desired state. Nothing was modified.

Examples
--------

**Minimal report:**

.. code-block:: yaml

    - name: Report result
      neubird.aap.report:
        status: remediated

**Full report with context and results:**

.. code-block:: yaml

    - name: Report remediation result to NeuBird
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: remediated
        changed_resources:
          - "{{ neubird_ctx.affected_resource }}"
        detail: "{{ remediation_task_result }}"

**Report a failure with diagnostic detail:**

.. code-block:: yaml

    - name: Report failure
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: failed
        detail:
          error: "Permission denied when attempting to disable key"
          key_id: "{{ neubird_ctx.affected_resource }}"

**Conditional status based on task outcome:**

.. code-block:: yaml

    - name: Report result
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: "{{ 'remediated' if rotation_result.changed else 'no_change' }}"
        changed_resources: "{{ [neubird_ctx.affected_resource] if rotation_result.changed else [] }}"
        detail: "{{ rotation_result }}"

.. note::

    ``neubird.aap.report`` always sets ``changed: false``. It is a reporting step,
    not a change step. It supports check mode and returns the report structure without
    writing it to job output when check mode is active.
