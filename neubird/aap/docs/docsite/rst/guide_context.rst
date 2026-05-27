.. _ansible_collections.neubird.aap.docsite.guide_context:

Reading NeuBird Investigation Context
======================================

When NeuBird AI triggers an AAP job, it passes investigation context as
``_neubird_context`` in the job's extra vars. The ``neubird.aap.context`` lookup
plugin makes that context available inside the playbook as a structured dict.

When the job was not triggered by NeuBird — for example, a manual run or a scheduled
job — the lookup returns ``null`` for all keys rather than failing. No special
handling is needed in your playbooks.

Context Keys
------------

``investigation_id``
    NeuBird investigation identifier. Example: ``inv-1234``.
    Used to correlate job results back to the originating investigation.

``severity``
    Severity level of the investigation. Example: ``high``, ``medium``, ``low``.

``affected_resource``
    The resource identifier that triggered the investigation.
    Example: ``sg-abc123``, ``arn:aws:iam::123456789012:user/compromised``.

``triggered_by``
    Originator of the job. ``neubird_ai`` when AI-triggered.

Usage
-----

Load context into a fact at the start of your playbook:

.. code-block:: yaml

    - name: Load NeuBird investigation context
      set_fact:
        neubird_ctx: "{{ lookup('neubird.aap.context') }}"

Then reference it in subsequent tasks:

.. code-block:: yaml

    - name: Disable the affected resource
      amazon.aws.iam_access_key:
        access_key_id: "{{ neubird_ctx.affected_resource }}"
        status: inactive

    - name: Report result
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: remediated

Graceful Degradation
--------------------

When the playbook is run manually (no ``_neubird_context`` in extra vars), all
context keys are ``null``. Use the ``default`` filter to handle this cleanly:

.. code-block:: yaml

    - name: Report result
      neubird.aap.report:
        investigation_id: "{{ neubird_ctx.investigation_id | default(omit) }}"
        status: remediated

.. note::

    Do not use ``neubird_ctx.investigation_id`` directly in conditionals without a
    default — it will evaluate to ``None`` (falsy) on manual runs, which is the
    correct and expected behaviour.

How Context Is Injected
-----------------------

NeuBird AI populates ``_neubird_context`` by passing it as extra vars when triggering
the job template via the AAP API. The variable name is fixed; do not rename it. If you
need to rename the fact for clarity, use:

.. code-block:: yaml

    - name: Load context
      set_fact:
        my_ctx: "{{ lookup('neubird.aap.context') }}"
