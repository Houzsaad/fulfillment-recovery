from dataclasses import dataclass
from enum import Enum


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

@dataclass
class Reservation:
    idempotency_key: str
    status: ReservationStatus
    quantity: int


class ReservationTimeout(Exception):
    pass


class ReservationService:

    def __init__(self):
        self.reservations = {}

    def get_reservation(self, idempotency_key: str):
        """Retrieve an existing reservation."""
        return self.reservations.get(idempotency_key)

    def create_reservation(
        self,
        idempotency_key: str,
        quantity: int,
        simulate_timeout: bool = False,
        simulate_failure: bool = False,
    ):
        """Create a reservation without duplicating existing operations."""

        # Reuse an existing operation with the same idempotency key.
        existing = self.get_reservation(idempotency_key)

        if existing:
            return existing

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        reservation = Reservation(
            idempotency_key=idempotency_key,
            status=ReservationStatus.PENDING,
            quantity=quantity,
        )

        # Simulate an external provider rejecting the request.
        if simulate_failure:
            reservation.status = ReservationStatus.FAILED
            self.reservations[idempotency_key] = reservation
            return reservation

        # Simulate the external provider successfully creating
        # the reservation, but our application receiving a timeout.
        self.reservations[idempotency_key] = reservation
        reservation.status = ReservationStatus.CONFIRMED

        if simulate_timeout:
            raise ReservationTimeout(
                "Reservation may have succeeded, but response timed out."
            )

        return reservation
