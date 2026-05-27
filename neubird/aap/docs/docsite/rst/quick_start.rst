.. _ansible_collections.neubird.aap.docsite.quick_start:

Quick Start
===========

The ``neubird.aap`` collection is an intelligence gateway between Ansible Automation
Platform (AAP) and NeuBird AI. It makes any existing job template AI-aware by adding
five components: safety tagging, context injection, pre-flight gating, structured
reporting, and audit logging.

NeuBird AI connects to AAP through AAP's MCP server. When an investigation is triggered,
NeuBird selects an appropriate job template, injects investigation context into the job's
extra vars, and reads the structured result back through MCP when the job completes.

Requirements
------------

- ansible-core >= 2.16.0
- Ansible Automation Platform >= 2.4
- Python >= 3.9

Installation
------------

Install from your Private Automation Hub:

.. code-block:: bash

    ansible-galaxy collection install neubird.aap

Or pin to a specific version:

.. code-block:: bash

    ansible-galaxy collection install neubird.aap==1.0.0

Add to a project's ``collections/requirements.yml``:

.. code-block:: yaml

    collections:
      - name: neubird.aap
        version: ">=1.0.0"

Admin Setup
-----------

Before NeuBird can auto-trigger a job template, an administrator must mark it as safe.
This is a one-time setup step per template:

.. code-block:: yaml

    - name: Mark the remediation template as safe for NeuBird
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

See :ref:`ansible_collections.neubird.aap.docsite.guide_tag_safe` for the full reference.

End-to-End Playbook Pattern
---------------------------

The following example shows all four in-playbook components working together. Place
this structure at the top and bottom of any playbook you want NeuBird to be able to
trigger:

.. code-block:: yaml

    ---
    - name: Rotate compromised IAM key
      hosts: localhost
      gather_facts: false

      tasks:
        # 1. Load NeuBird investigation context (null-safe when not AI-triggered)
        - name: Load investigation context
          set_fact:
            neubird_ctx: "{{ lookup('neubird.aap.context') }}"

        # 2. Gate on safety conditions before making any changes
        - name: Pre-flight safety checks
          neubird.aap.preflight:
            check_maintenance_window: true
            maintenance_window_start: "02:00"
            maintenance_window_end: "04:00"
            check_conflicting_jobs: true
            controller_host: "https://aap.example.com"
            controller_token: "{{ lookup('env', 'AAP_TOKEN') }}"
            template_name: "Rotate IAM Key"

        # 3. Your existing remediation tasks — unchanged
        - name: Disable the compromised IAM key
          amazon.aws.iam_access_key:
            access_key_id: "{{ neubird_ctx.affected_resource }}"
            status: inactive
          register: iam_result

        # 4. Write a compliance audit record
        - name: Write audit record
          neubird.aap.audit:
            action: "iam_key_disabled"
            triggered_by: "{{ neubird_ctx.triggered_by | default('manual') }}"
            investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
            destination: syslog

        # 5. Report structured results back to NeuBird via MCP
        - name: Report result to NeuBird
          neubird.aap.report:
            investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
            status: remediated
            changed_resources:
              - "{{ neubird_ctx.affected_resource }}"
            detail: "{{ iam_result }}"

Graceful Degradation
--------------------

All five components degrade gracefully when a job is run manually (not triggered by
NeuBird). The ``context`` lookup returns ``null`` for all keys, ``preflight`` skips
checks that have no parameters, ``report`` omits the ``investigation_id``, and
``audit`` records ``triggered_by: manual``. No special handling is needed in your
playbooks.
