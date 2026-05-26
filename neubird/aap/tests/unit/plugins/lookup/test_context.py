# tests/unit/plugins/lookup/test_context.py


def test_context_returns_empty_when_no_vars():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables={})
    assert result == [{
        'investigation_id': None,
        'severity': None,
        'affected_resource': None,
        'triggered_by': None,
    }]


def test_context_returns_injected_values():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    ctx = {
        'investigation_id': 'inv-1234',
        'severity': 'high',
        'affected_resource': 'sg-abc123',
        'triggered_by': 'neubird_ai',
    }
    result = lookup.run([], variables={'_neubird_context': ctx})
    assert result == [ctx]


def test_context_fills_missing_keys():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables={'_neubird_context': {'investigation_id': 'inv-5'}})
    assert result[0]['investigation_id'] == 'inv-5'
    assert result[0]['severity'] is None
    assert result[0]['affected_resource'] is None
    assert result[0]['triggered_by'] is None


def test_context_graceful_with_none_variables():
    from ansible_collections.neubird.aap.plugins.lookup.context import LookupModule
    lookup = LookupModule()
    result = lookup.run([], variables=None)
    assert result[0]['investigation_id'] is None
