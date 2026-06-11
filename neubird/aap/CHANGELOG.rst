================================
neubird.aap Release Notes
================================

.. contents:: Topics

v1.1.0
======

Minor Changes
-------------

- Added ``neubird_client`` module_utils providing shared NeuBird API
  authentication, investigation trigger, and session-retrieval helpers.

New Modules
-----------

- neubird.aap.investigate - Trigger a NeuBird AI investigation from an Ansible playbook.
- neubird.aap.investigation_result - Retrieve the status and findings of a NeuBird investigation.

v1.0.4
======

Bugfixes
--------

- Fixed ``tag_safe`` module API path from ``/api/v2/`` to ``/api/controller/v2/``
  for compatibility with AAP 2.5+ Platform Gateway routing.

v1.0.3
======

Bugfixes
--------

- Fixed ``tag_safe`` module URL-encoding template names containing spaces,
  preventing ``URL can't contain control characters`` errors.

v1.0.2
======

Bugfixes
--------

- Added ``.ansible-lint`` config to exclude ``docs/docsite/`` from linting,
  eliminating false-positive ``load-failure`` warnings during hub import.
- Cleaned up ``build_ignore`` in ``galaxy.yml`` to exclude tooling artifacts
  (``.ansible``, ``.claude``, ``.pytest_cache``, ``importer_result.json``)
  from the published tarball.

v1.0.1
======

Bugfixes
--------

- Added ``docs/docsite/`` RST structure (``extra-docs.yml`` and six guide
  files) to support hub documentation rendering.
- Bumped version from 1.0.0 to allow re-upload to automation hub after
  initial 1.0.0 import completed without a valid ``docs_blob``.

v1.0.0
======

New Modules
-----------

- ``neubird.aap.report`` - Report remediation results to NeuBird AI.
- ``neubird.aap.tag_safe`` - Mark an AAP job template as safe for NeuBird automated remediation.
- ``neubird.aap.preflight`` - Run pre-flight safety checks before NeuBird-triggered jobs.
- ``neubird.aap.audit`` - Write a structured audit record for NeuBird-triggered remediation.

New Lookup Plugins
------------------

- ``neubird.aap.context`` - Read NeuBird investigation context from AAP job variables.
