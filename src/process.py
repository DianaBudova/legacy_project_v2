"""Order orchestration with isolated financial rules and compatible output."""
from collections import Counter
from enum import Enum, IntEnum

from src.db import get_data, save
from src.utils import calc, format_date


class Role(IntEnum):
    """Known user roles; any other role uses the standard tax policy."""

    REGULAR = 2
    PREMIUM = 3


class OrderStatus(str, Enum):
    """Persisted order states, including the legacy validation-only refund."""

    PAID = "paid"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PROCESSED = "processed"


STANDARD_TAX_RATE = 0.20
PREMIUM_TAX_RATE = 0.15
PREMIUM_DISCOUNT_TIERS = ((1000, 0.05), (500, 0.03))
VALID_STATUSES = tuple(status.value for status in OrderStatus
                       if status != OrderStatus.PROCESSED)
REQUIRED_FIELDS = ("user_id", "product_id", "status")


def proc(params=None):
    """Load, process and save orders; retain the unused legacy params argument."""
    del params
    orders = get_data("orders")
    users = _index_by_id(get_data("users"))
    products = _index_by_id(get_data("products"))
    records, errors = [], []
    for order in orders:
        record, error = _process_order(order, users, products)
        if error is not None:
            errors.append(error)
        else:
            records.append(record)
    summary = _summarize(records, errors)
    save("processed_orders", records)
    save("summary", summary)
    return {"orders": records, "summary": summary}


def _index_by_id(items):
    """Index hashable entity IDs, preserving the first duplicate as before."""
    indexed = {}
    for item in items:
        indexed.setdefault(item["id"], item)
    return indexed


def _process_order(order, users, products):
    """Resolve references and dispatch an order, preserving error precedence."""
    user = users.get(order["user_id"])
    if user is None:
        return None, {"order_id": order["id"], "error": "user not found"}
    if order["product_id"] not in products:
        return None, {"order_id": order["id"], "error": "product not found"}
    status = order["status"]
    if status == OrderStatus.PAID:
        return _paid_order(order, user), None
    if status in (OrderStatus.PENDING, OrderStatus.CANCELLED):
        return _order_record(order, user, status), None
    return None, {"order_id": order["id"], "error": f"unknown status: {status}"}


def _order_record(order, user, status):
    """Format the common output fields without modifying the input order."""
    return {
        "order_id": order["id"], "user": user["name"],
        "amount": 0 if status == OrderStatus.CANCELLED else order["amount"],
        "status": status, "date": format_date(order["date"]),
    }


def _paid_order(order, user):
    """Apply the single tax and discount policy to one paid order."""
    amount = order["amount"]
    tax = calculate_tax(amount, user["role"])
    discount = get_discount(amount, user["role"])
    record = _order_record(order, user, OrderStatus.PROCESSED.value)
    record.update(tax=tax, discount=discount, net=amount-discount-tax)
    return record


def _summarize(records, errors):
    """Aggregate result counts and rounded totals, retaining record order."""
    counts = Counter(record["status"] for record in records)
    return {
        "processed": counts[OrderStatus.PROCESSED],
        "pending": counts[OrderStatus.PENDING],
        "cancelled": counts[OrderStatus.CANCELLED],
        "total_revenue": round(sum(record.get("net", 0) for record in records), 2),
        "total_tax": round(sum(record.get("tax", 0) for record in records), 2),
        "errors": errors,
    }


def _validation_checks(order):
    """Yield checks lazily to retain first-error order and legacy exceptions."""
    yield "amount" in order, "no amount"
    yield not order.get("amount", 0) <= 0, "invalid amount"
    yield from ((key in order, f"no {key}") for key in REQUIRED_FIELDS)
    yield order["status"] in VALID_STATUSES, f"invalid status: {order['status']}"


def validate_order(o):
    """Return (valid, first error) with the existing permissive validation rules."""
    if not o:
        return False, "empty order"
    error = next((message for valid, message in _validation_checks(o) if not valid), None)
    return error is None, error


def calculate_tax(amount, role):
    """Return tax rounded by calc(), using the premium or standard rate."""
    rate = PREMIUM_TAX_RATE if role == Role.PREMIUM else STANDARD_TAX_RATE
    return calc(amount, rate)


def get_discount(amount, role):
    """Return premium discounts with strict thresholds and existing rounding."""
    if role != Role.PREMIUM:
        return 0
    for threshold, rate in PREMIUM_DISCOUNT_TIERS:
        if amount > threshold:
            return calc(amount, rate)
    return 0
