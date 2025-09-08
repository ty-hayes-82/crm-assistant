"""
Test that the deprecated A2A wrapper properly raises ImportError.
This prevents accidental re-introduction of the legacy wrapper.
"""

import pytest


def test_deprecated_a2a_wrapper_raises_import_error():
    """Test that importing the deprecated a2a_wrapper raises ImportError."""
    with pytest.raises(ImportError, match="Deprecated: use crm_agent.a2a.agent.create_crm_a2a_agent"):
        import crm_agent.a2a_wrapper


def test_deprecated_wrapper_function_raises_import_error():
    """Test that importing the deprecated wrapper function raises ImportError."""
    with pytest.raises(ImportError, match="Deprecated: use crm_agent.a2a.agent.create_crm_a2a_agent"):
        from crm_agent.a2a_wrapper import create_crm_a2a_agent
