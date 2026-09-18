from __future__ import annotations

import pytest
from hls_manifest import validate_manifest

from hls_lpdaac.cnm import ProviderAlreadySetError, add_provider

from .conftest import CNM_MANIFEST

PROVIDER = "lp_HLS_2.0_FORWARD_PROCESSED"


def test_the_fixture_is_a_valid_cnm_manifest() -> None:
    # Guards the tests below: a fixture that fails the schema on its own would
    # make the round-trip test vacuous.
    validate_manifest(CNM_MANIFEST)


def test_adds_the_provider() -> None:
    result = add_provider(CNM_MANIFEST, PROVIDER)

    assert result["provider"] == PROVIDER


def test_does_not_mutate_the_input() -> None:
    add_provider(CNM_MANIFEST, PROVIDER)

    assert "provider" not in CNM_MANIFEST


def test_preserves_every_other_field() -> None:
    result = add_provider(CNM_MANIFEST, PROVIDER)

    assert {k: v for k, v in result.items() if k != "provider"} == CNM_MANIFEST


def test_output_still_validates_against_the_cnm_schema() -> None:
    validate_manifest(add_provider(CNM_MANIFEST, PROVIDER))


def test_rejects_a_manifest_that_already_has_a_provider() -> None:
    manifest = {**CNM_MANIFEST, "provider": "lp_HLS_2.0_BACKWARD_PROCESSED"}

    with pytest.raises(ProviderAlreadySetError):
        add_provider(manifest, PROVIDER)
