
from dataclasses import dataclass
from enum import Enum


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class ReleaseStatus(Enum):
    PENDING = "pending"
    RELEASED = "released"
    FAILED = "failed"


@dataclass
class Reservation:
    idempotency_key: str
    status: ReservationStatus
    quantity: int
    release_status: ReleaseStatus | None = None


class ReservationTimeout(Exception):
    pass


class ReservationReleaseTimeout(Exception):
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

        if simulate_failure:
            reservation.status = ReservationStatus.FAILED
            self.reservations[idempotency_key] = reservation
            return reservation

        self.reservations[idempotency_key] = reservation
        reservation.status = ReservationStatus.CONFIRMED

        if simulate_timeout:
            raise ReservationTimeout(
                "Reservation may have succeeded, but response timed out."
            )

        return reservation

    def release_reservation(
        self,
        idempotency_key: str,
        simulate_timeout: bool = False,
        simulate_failure: bool = False,
    ):
        """Release an existing reservation without duplicating the operation."""

        reservation = self.get_reservation(idempotency_key)

        if reservation is None:
            return None

        if reservation.status != ReservationStatus.CONFIRMED:
            raise ValueError("Only confirmed reservations can be released.")

        # Reuse an existing release outcome.
        if reservation.release_status is not None:
            return reservation

        reservation.release_status = ReleaseStatus.PENDING

        if simulate_failure:
            reservation.release_status = ReleaseStatus.FAILED
            return reservation

        # Simulate successful release by the external provider.
        reservation.release_status = ReleaseStatus.RELEASED

        if simulate_timeout:
            raise ReservationReleaseTimeout(
                "Reservation release may have succeeded, but response timed out."
            )

        return reservation
