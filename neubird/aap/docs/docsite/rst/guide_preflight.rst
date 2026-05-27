.. _ansible_collections.neubird.aap.docsite.guide_preflight:

Pre-Flight Safety Checks
========================

``neubird.aap.preflight`` runs safety checks at the start of a playbook before any
changes are made. If any check fails, the play stops immediately with a structured
error that NeuBird AI can parse through its MCP connection.

Place ``neubird.aap.preflight`` as the **first task** in any playbook tagged for
automated remediation. It makes no changes to the system and supports check mode.

Available Checks
----------------

Maintenance Window
~~~~~~~~~~~~~~~~~~

Fails if the current UTC time falls within a defined maintenance window. Supports
overnight windows (e.g., 22:00 to 02:00).

.. code-block:: yaml

    - name: Pre-flight checks
      neubird.aap.preflight:
        check_maintenance_window: true
        maintenance_window_start: "02:00"
        maintenance_window_end: "04:00"

Both ``maintenance_window_start`` and ``maintenance_window_end`` are required when
``check_maintenance_window`` is ``true``. Times are in HH:MM UTC format.

Conflicting Jobs
~~~~~~~~~~~~~~~~

Fails if another job using the same template is currently running on the AAP
controller. Prevents concurrent automated remediations on the same target.

.. code-block:: yaml

    - name: Pre-flight checks
      neubird.aap.preflight:
        check_conflicting_jobs: true
        controller_host: "https://aap.example.com"
        controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
        template_name: "Rotate IAM Key"

``controller_host``, ``controller_token``, and ``template_name`` are all required when
``check_conflicting_jobs`` is ``true``. ``controller_token`` is never logged.

Target Host Reachability
~~~~~~~~~~~~~~~~~~~~~~~~

Verifies a target host is reachable on port 22 before proceeding. Useful for
remediations that SSH to a managed node.

.. code-block:: yaml

    - name: Pre-flight checks
      neubird.aap.preflight:
        target_host: "{{ inventory_hostname }}"

Combining Checks
----------------

All checks can be combined in a single task. The module runs each check that has
its required parameters present and collects all failures before calling ``fail_json``,
so you see every failing check at once rather than one at a time:

.. code-block:: yaml

    - name: Full pre-flight safety gate
      neubird.aap.preflight:
        check_maintenance_window: true
        maintenance_window_start: "02:00"
        maintenance_window_end: "04:00"
        check_conflicting_jobs: true
        controller_host: "https://aap.example.com"
        controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
        template_name: "Rotate IAM Key"
        target_host: "{{ inventory_hostname }}"

Return Values
-------------

On success, ``checks`` contains a ``pass`` or ``fail`` entry for each check that ran:

.. code-block:: json

    {
      "checks": {
        "maintenance_window": "pass",
        "conflicting_jobs": "pass",
        "target_host": "pass"
      }
    }

On failure, ``neubird_preflight_failed: true`` is set alongside the ``checks`` dict
so NeuBird AI can distinguish a pre-flight block from other playbook failures.
