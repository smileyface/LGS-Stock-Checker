from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


# Define as a Table object, not an ORM class
user_store_preferences = Table(
    "user_store_preferences",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("store_id", Integer, ForeignKey("stores.id"), primary_key=True)
)


# Users Table (Updated)
class User(UserMixin, Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Relationship to stores (User's selected stores)
    selected_stores = relationship("Store", secondary=user_store_preferences, backref="users")

    # Relationship to the cards the user is tracking
    cards = relationship("UserTrackedCards", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Returns user data as a dictionary, suitable for JSON responses."""
        return {
            'id': self.id,
            'username': self.username,
            # This now correctly uses the relationship to get the store slugs
            'stores': [store.slug for store in self.selected_stores]
        }


class Card(Base):
    __tablename__ = "cards"
    name = Column(String, primary_key=True, index=True)


class Set(Base):
    """Represents a card set in the database."""
    __tablename__ = "sets"
    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    release_date = Column(Date, nullable=True)


class UserTrackedCards(Base):
    __tablename__ = "user_tracked_cards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_name = Column(String, ForeignKey("cards.name"), nullable=False)
    amount = Column(Integer, nullable=False)

    # Relationship to specifications (one-to-many)
    specifications = relationship("CardSpecification", back_populates="user_card", cascade="all, delete-orphan")

    # Relationship back to the user
    user = relationship("User", back_populates="cards")


class CardSpecification(Base):
    __tablename__ = "card_specifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_card_id = Column(Integer, ForeignKey("user_tracked_cards.id"), nullable=False)
    set_code = Column(String, nullable=True)  # NULL = "Any Set"
    collector_number = Column(String, nullable=True)  # NULL = "Any Collector Number"
    finish = Column(String, nullable=True)  # NULL = "Any Finish"

    # Relationship back to user_card_preferences
    user_card = relationship("UserTrackedCards", back_populates="specifications")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Ensure unique store names
    slug = Column(String, nullable=False, unique=True)  # Short identifier, unique
    homepage = Column(String, nullable=False)  # Store website
    search_url = Column(String, nullable=False)  # Search page URL
    fetch_strategy = Column(String, nullable=False)  # Type of fetching strategy

    def __repr__(self):
        return f"<Store(name={self.name}, slug={self.slug}, strategy={self.fetch_strategy})>"
