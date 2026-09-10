================================
neubird.aap Release Notes
================================

.. contents:: Topics

v1.1.1
======

Minor Changes
-------------

- Updated all documentation and module metadata to use the current company
  name ``NeuBird`` in place of the retired ``NeuBird AI``.
- Corrected the documented minimum Ansible Automation Platform version from
  2.4 to 2.5. The ``tag_safe`` and ``preflight`` modules require Platform
  Gateway routing (``/api/controller/v2/``), which AAP 2.4 does not provide.
  ``tag_safe`` has required 2.5 since v1.0.4; the documentation had not caught up.

Bugfixes
--------

- Fixed ``tag_safe`` silently discarding a job template's existing
  ``extra_vars`` when they were stored as YAML. AAP accepts both JSON and YAML
  in this field and the web UI writes YAML by default, but the module parsed
  only JSON and fell back to an empty dict on failure, so the subsequent PATCH
  replaced every existing variable with just the NeuBird tag. The module now
  reads both formats and fails without writing if the content cannot be parsed
  or is not a mapping.
- Fixed ``preflight`` module URL-encoding template names containing spaces,
  preventing ``URL can't contain control characters`` errors. This is the same
  fix applied to ``tag_safe`` in v1.0.3.
- Fixed ``preflight`` module API path from ``/api/v2/`` to
  ``/api/controller/v2/`` for compatibility with AAP 2.5+ Platform Gateway
  routing. This is the same fix applied to ``tag_safe`` in v1.0.4.
- Fixed ``tests/unit/conftest.py`` importing the deprecated
  ``ansible.module_utils._text``, which aborted ``ansible-test units``
  collection on ansible-core 2.20. Now imports ``to_bytes`` from
  ``ansible.module_utils.common.text.converters``.

v1.1.0
======

Minor Changes
-------------

- Added ``neubird_client`` module_utils providing shared NeuBird API
  authentication, investigation trigger, and session-retrieval helpers.

New Modules
-----------

- neubird.aap.investigate - Trigger a NeuBird investigation from an Ansible playbook.
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

- ``neubird.aap.report`` - Report remediation results to NeuBird.
- ``neubird.aap.tag_safe`` - Mark an AAP job template as safe for NeuBird automated remediation.
- ``neubird.aap.preflight`` - Run pre-flight safety checks before NeuBird-triggered jobs.
- ``neubird.aap.audit`` - Write a structured audit record for NeuBird-triggered remediation.

New Lookup Plugins
------------------

- ``neubird.aap.context`` - Read NeuBird investigation context from AAP job variables.
