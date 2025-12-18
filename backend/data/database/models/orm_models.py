from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    Date,
    UniqueConstraint,
)
from typing import Any
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

printing_finish_association = Table(
    "printing_finish_association",
    Base.metadata,
    Column(
        "printing_id",
        Integer,
        ForeignKey("card_printings.id"),
        primary_key=True,
    ),
    Column("finish_id", Integer, ForeignKey("finishes.id"), primary_key=True),
)


# Define as a Table object, not an ORM class
user_store_preferences = Table(
    "user_store_preferences",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("store_id", Integer, ForeignKey("stores.id"), primary_key=True),
)


# Users Table
class User(UserMixin, Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Relationship to stores (User's selected stores)
    selected_stores = relationship(
        "Store", secondary=user_store_preferences, backref="users"
    )

    # Relationship to the cards the user is tracking
    cards = relationship(
        "UserTrackedCards", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, username: str,
                 password_hash: str,
                 **kw: Any):
        super().__init__(**kw)
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(str(self.password_hash), password)

    def to_dict(self):
        """Returns user data as a dictionary, suitable for JSON responses."""
        return {
            "id": self.id,
            "username": self.username,
            # This now correctly uses the relationship to get the store slugs
            "stores": [store.slug for store in self.selected_stores],
            "cards": [cards.to_dict() for cards in self.cards],
        }


class Card(Base):
    __tablename__ = "cards"
    name = Column(String, primary_key=True, index=True)

    def __repr__(self):
        return f"<Card(name={self.name})>"

    def to_dict(self):
        return {"name": self.name}


class Set(Base):
    """Represents a card set in the database."""

    __tablename__ = "sets"
    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    release_date = Column(Date, nullable=True)

    def __repr__(self):
        return f"<Set(code={self.code}, name={self.name})>"

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name
        }


class Finish(Base):
    """Represents a card finish type (e.g., Foil, Non-Foil)."""

    __tablename__ = "finishes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Finish(name={self.name})>"

    def to_dict(self):
        return {"name": self.name,
                "id": self.id}


class CardPrinting(Base):
    """Represents a unique physical printing of a card."""

    __tablename__ = "card_printings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String, ForeignKey("cards.name"), nullable=False)
    set_code = Column(String, ForeignKey("sets.code"), nullable=False)
    collector_number = Column(String, nullable=False)

    # Relationships
    card = relationship("Card")
    set = relationship("Set")
    available_finishes = relationship(
        "Finish", secondary=printing_finish_association
    )

    __table_args__ = (
        UniqueConstraint(
            "card_name",
            "set_code",
            "collector_number",
            name="_card_printing_uc",
        ),
    )


class UserTrackedCards(Base):
    __tablename__ = "user_tracked_cards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_name = Column(String, ForeignKey("cards.name"), nullable=False)
    amount = Column(Integer, nullable=False)

    # Relationship to specifications (one-to-many)
    specifications = relationship(
        "CardSpecification",
        back_populates="user_card",
        cascade="all, delete-orphan",
    )

    # Relationship back to the user
    user = relationship("User", back_populates="cards")

    # Relationship to the card itself
    card = relationship("Card")

    def __repr__(self):
        return (f"<UserTrackedCards(user_id={self.user_id}, "
                f"card_name={self.card_name}, amount={self.amount})>")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.card_name,
            "amount": self.amount,
            "specifications": [
                spec.to_dict() for spec in self.specifications
            ],
        }


class CardSpecification(Base):
    __tablename__ = "card_specifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_card_id = Column(
        Integer, ForeignKey("user_tracked_cards.id", ondelete="CASCADE"), nullable=False
    )
    set_code = Column(String, ForeignKey("sets.code"), nullable=True)
    collector_number = Column(
        String, nullable=True
    )  # NULL = "Any Collector Number"
    finish_id = Column(Integer, ForeignKey("finishes.id"), nullable=True)

    # Relationship back to user_card_preferences
    user_card = relationship(
        "UserTrackedCards", back_populates="specifications"
    )
    finish = relationship("Finish")
    set = relationship("Set")

    def __repr__(self):
        return (f"<CardSpecification(user_card_id={self.user_card_id},"
                f" set_code={self.set_code}, "
                f" collector_number={self.collector_number},"
                f" finish_id={self.finish_id})>")

    def to_dict(self):
        return {
            "set_code": self.set_code,
            "collector_number": self.collector_number,
            "finish": self.finish.to_dict()["name"] if self.finish else None,
        }


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String, nullable=False, unique=True
    )  # Ensure unique store names
    slug = Column(
        String, nullable=False, unique=True
    )  # Short identifier, unique
    homepage = Column(String, nullable=False)  # Store website
    search_url = Column(String, nullable=False)  # Search page URL
    fetch_strategy = Column(String, nullable=False)

    def __repr__(self):
        return f"<Store(name={self.name},\
                slug={self.slug}, \
                strategy={self.fetch_strategy})>"
