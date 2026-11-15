"""Local chain results must distinguish no evidence from a checked match."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/python'))
from vcp_crypto_shredding import EventType, VCPCryptoShredder, demo_crypto_shredding


def test_empty_chain_is_unresolved_and_does_not_create_events():
    shredder = VCPCryptoShredder()
    result = shredder.verify_chain_integrity()
    assert result['verified'] is False
    assert result['status'] == 'INDETERMINATE'
    assert result['result_scope'] == 'LOCAL_PAYLOAD_HASH_CHAIN'
    assert result['events_checked'] == 0
    assert result['errors'] == []
    assert shredder.get_chain() == []
    assert datetime.fromisoformat(result['verified_at'].replace('Z', '+00:00')).tzinfo == timezone.utc


def test_nonempty_match_and_local_key_removal_keep_the_bounded_scope():
    shredder = VCPCryptoShredder()
    shredder.create_event(EventType.ORD, {'symbol': 'SYNTHETIC'}, [], 'synthetic-subject')
    before = copy.deepcopy([event.to_dict() for event in shredder.get_chain()])
    result = shredder.verify_chain_integrity()
    assert result['verified'] is True
    assert result['status'] == 'VALID'
    assert result['result_scope'] == 'LOCAL_PAYLOAD_HASH_CHAIN'
    assert datetime.fromisoformat(result['verified_at'].replace('Z', '+00:00')).tzinfo == timezone.utc
    assert [event.to_dict() for event in shredder.get_chain()] == before
    shredder.execute_erasure('synthetic-subject')
    assert shredder.verify_chain_integrity()['status'] == 'VALID'


def test_payload_mismatch_is_invalid_and_verification_preserves_input():
    shredder = VCPCryptoShredder()
    event = shredder.create_event(EventType.ORD, {'symbol': 'SYNTHETIC'}, [], 'synthetic-subject')
    event.payload['symbol'] = 'changed'
    before = copy.deepcopy(event.to_dict())
    result = shredder.verify_chain_integrity()
    assert result['verified'] is False
    assert result['status'] == 'INVALID'
    assert result['errors'][0]['error'] == 'EVENT_HASH_MISMATCH'
    assert event.to_dict() == before


def test_existing_demo_keeps_local_results_and_its_explicit_limits(capsys):
    shredder, certificate = demo_crypto_shredding()
    output = capsys.readouterr().out
    result = shredder.verify_chain_integrity()
    assert result['status'] == 'VALID'
    assert result['result_scope'] == 'LOCAL_PAYLOAD_HASH_CHAIN'
    assert result['events_checked'] == 4
    assert certificate.keys_destroyed == 1
    assert 'Retained copies and memory zeroization are not assessed.' in output
    assert 'compliance is not determined.' in output
