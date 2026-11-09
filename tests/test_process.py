"""Characterization and boundary tests for the public order-processing contract."""
from copy import deepcopy
from unittest.mock import Mock, call

import pytest

from src import process


@pytest.fixture
def storage(monkeypatch):
    """Replace persistence with an isolated in-memory boundary."""
    data = {
        'orders': [],
        'users': [{'id': 1, 'name': 'First user', 'role': 3}],
        'products': [{'id': 10}],
    }
    monkeypatch.setattr(process, 'get_data', lambda name: data[name])
    save = Mock()
    monkeypatch.setattr(process, 'save', save)
    return data, save


def order(**changes):
    """Build a complete order with independently replaceable fields."""
    return dict(id=101, user_id=1, product_id=10, amount=1200,
                status='paid', date='2024-01-15', **{}) | changes


@pytest.mark.parametrize('role', [3, 2, 1, 4, None, '3'])
@pytest.mark.parametrize('amount,premium_discount', [
    (0, 0), (500, 0), (500.01, 15), (1000, 30), (1000.01, 50), (1200, 60),
])
def test_paid_roles_and_discount_boundaries(storage, role, amount, premium_discount):
    """Every role retains taxes, strict thresholds, rounding and output fields."""
    data, save = storage
    data['orders'] = [order(amount=amount)]
    data['users'][0]['role'] = role
    before = deepcopy(data)
    result = process.proc({'legacy_unused_parameter': True})
    tax = round(amount * (0.15 if role == 3 else 0.2), 2)
    discount = premium_discount if role == 3 else 0
    expected = {'order_id': 101, 'user': 'First user', 'amount': amount,
                'discount': discount, 'tax': tax, 'net': amount-discount-tax,
                'status': 'processed', 'date': '15.01.2024'}
    assert result == {'orders': [expected], 'summary': {
        'processed': 1, 'pending': 0, 'cancelled': 0,
        'total_revenue': round(expected['net'], 2), 'total_tax': tax, 'errors': []}}
    assert save.call_args_list == [call('processed_orders', [expected]),
                                   call('summary', result['summary'])]
    assert data == before


@pytest.mark.parametrize('role,expected_tax,expected_discount', [
    (3, 180, 60), (2, 240, 0), (4, 240, 0), (None, 240, 0),
])
def test_public_financial_helpers(role, expected_tax, expected_discount):
    """Existing financial entry points remain available and compatible."""
    assert process.calculate_tax(1200, role) == expected_tax
    assert process.get_discount(1200, role) == expected_discount


@pytest.mark.parametrize('status,amount', [('pending', 1200), ('cancelled', 0)])
def test_non_paid_statuses(storage, status, amount):
    data, _ = storage
    data['orders'] = [order(status=status)]
    result = process.proc()
    assert result['orders'] == [{'order_id': 101, 'user': 'First user',
                                'amount': amount, 'status': status, 'date': '15.01.2024'}]
    assert result['summary'][status] == 1
    assert result['summary']['total_revenue'] == result['summary']['total_tax'] == 0


@pytest.mark.parametrize('status', ['refunded', 'unknown', '', None])
def test_unknown_processing_status_including_refunded(storage, status):
    data, _ = storage
    data['orders'] = [order(status=status)]
    result = process.proc()
    assert result['orders'] == []
    assert result['summary']['errors'] == [
        {'order_id': 101, 'error': f'unknown status: {status}'}]


@pytest.mark.parametrize('users,products,message', [
    ([], [], 'user not found'), ([], [{'id': 10}], 'user not found'),
    ([{'id': 1, 'name': 'First user', 'role': 3}], [], 'product not found'),
])
def test_missing_references_preserve_error_priority(storage, users, products, message):
    data, _ = storage
    data.update(orders=[order()], users=users, products=products)
    result = process.proc()
    assert result['orders'] == []
    assert result['summary']['errors'] == [{'order_id': 101, 'error': message}]


def test_first_duplicate_user_wins(storage):
    data, _ = storage
    data['orders'] = [order()]
    data['users'].append({'id': 1, 'name': 'Second user', 'role': 2})
    data['products'].append({'id': 10})
    result = process.proc()['orders'][0]
    assert result['user'] == 'First user'
    assert result['tax'] == 180


def test_empty_orders_are_saved(storage):
    _, save = storage
    result = process.proc()
    assert result == {'orders': [], 'summary': {'processed': 0, 'pending': 0,
        'cancelled': 0, 'total_revenue': 0, 'total_tax': 0, 'errors': []}}
    assert save.call_count == 2


def test_mixed_batch_and_invalid_date(storage):
    data, _ = storage
    data['orders'] = [order(), order(id=102, status='pending', date='invalid'),
                      order(id=103, status='cancelled'),
                      order(id=104, user_id=999), order(id=105, status='refunded')]
    result = process.proc()
    assert [r['order_id'] for r in result['orders']] == [101, 102, 103]
    assert result['orders'][1]['date'] == 'invalid'
    assert result['summary'] == {'processed': 1, 'pending': 1, 'cancelled': 1,
        'total_revenue': 960, 'total_tax': 180, 'errors': [
            {'order_id': 104, 'error': 'user not found'},
            {'order_id': 105, 'error': 'unknown status: refunded'}]}


@pytest.mark.parametrize('value,expected', [
    (None, (False, 'empty order')), ({}, (False, 'empty order')),
    ({'status': 'paid'}, (False, 'no amount')),
    ({'amount': 0}, (False, 'invalid amount')),
    ({'amount': -0.01}, (False, 'invalid amount')),
    ({'amount': 0.01}, (False, 'no user_id')),
    ({'amount': 1, 'user_id': 1}, (False, 'no product_id')),
    ({'amount': 1, 'user_id': 1, 'product_id': 10}, (False, 'no status')),
    (order(status='invalid'), (False, 'invalid status: invalid')),
    (order(status=''), (False, 'invalid status: ')),
    (order(status=None), (False, 'invalid status: None')),
    (order(amount=0.01), (True, None)),
    (order(amount=500), (True, None)), (order(amount=1000), (True, None)),
    (order(status='pending'), (True, None)),
    (order(status='cancelled'), (True, None)),
    (order(status='refunded'), (True, None)),
    (order(user_id=None, product_id=None), (True, None)),
    (order(amount=float('nan')), (True, None)),
])
def test_validation_boundaries_and_error_order(value, expected):
    """Validate the old contract, including permissive values and first error."""
    assert process.validate_order(value) == expected


@pytest.mark.parametrize('amount', [None, '100'])
def test_invalid_amount_types_keep_type_error(amount):
    with pytest.raises(TypeError):
        process.validate_order(order(amount=amount))
