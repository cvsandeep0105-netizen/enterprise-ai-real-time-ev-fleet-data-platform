from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    String,
    Text,
    UniqueConstraint,
)

from app.database.database import Base


class Telemetry(Base):
    """
    Canonical persisted EV telemetry event.

    Database table:
        ev_data

    Responsibilities:
        - Store immutable telemetry events
        - Preserve event identity
        - Support vehicle/time-series queries
        - Support downstream analytics
    """

    __tablename__ = "ev_data"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # --------------------------------------------------------
    # EVENT IDENTITY
    # --------------------------------------------------------

    event_id = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
    )

    schema_version = Column(
        String(20),
        nullable=False,
    )

    producer = Column(
        String(100),
        nullable=False,
    )

    # --------------------------------------------------------
    # VEHICLE
    # --------------------------------------------------------

    vehicle_id = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # TELEMETRY
    # --------------------------------------------------------

    battery = Column(
        Float,
        nullable=False,
    )

    temp = Column(
        Float,
        nullable=False,
    )

    speed = Column(
        Float,
        nullable=False,
    )

    location = Column(
        String(100),
        nullable=True,
    )

    charging_status = Column(
        String(30),
        nullable=True,
    )

    # --------------------------------------------------------
    # EVENT TIME
    # --------------------------------------------------------

    timestamp = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    ingestion_timestamp = Column(
        DateTime,
        nullable=True,
    )

    # --------------------------------------------------------
    # DERIVED ATTRIBUTES
    # --------------------------------------------------------

    battery_status = Column(
        String(20),
        nullable=True,
    )

    vehicle_status = Column(
        String(20),
        nullable=True,
    )

    temperature_status = Column(
        String(20),
        nullable=True,
    )

    is_charging = Column(
        Boolean,
        nullable=True,
    )

    # --------------------------------------------------------
    # TABLE CONSTRAINTS / INDEXES
    # --------------------------------------------------------

    __table_args__ = (
        UniqueConstraint(
            "vehicle_id",
            "timestamp",
            name="uq_ev_data_vehicle_timestamp",
        ),

        Index(
            "idx_ev_data_vehicle_timestamp",
            "vehicle_id",
            "timestamp",
        ),
    )


class Alert(Base):
    """
    EV operational alert lifecycle record.

    Alert states:
        ACTIVE
        RESOLVED
    """

    __tablename__ = "alerts"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    vehicle_id = Column(
        String(50),
        nullable=False,
        index=True,
    )

    alert_type = Column(
        String(50),
        nullable=False,
    )

    alert_value = Column(
        Float,
        nullable=True,
    )

    severity = Column(
        String(30),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    timestamp = Column(
        DateTime,
        nullable=False,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "idx_alerts_vehicle_status_timestamp",
            "vehicle_id",
            "status",
            "timestamp",
        ),
    )


class Vehicle(Base):
    """
    EV fleet vehicle master record.
    """

    __tablename__ = "vehicles"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    vehicle_id = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    battery = Column(
        Float,
        nullable=True,
    )

    speed = Column(
        Float,
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=True,
    )


class User(Base):
    """
    Enterprise authentication user.

    Passwords are stored only as secure password hashes.
    """

    __tablename__ = "users"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )
