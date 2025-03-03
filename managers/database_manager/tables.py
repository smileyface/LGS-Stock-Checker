from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Define as a Table object, not an ORM class
user_store_preferences = Table(
    "user_store_preferences",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("store_id", Integer, ForeignKey("stores.id"), primary_key=True)
)


# Users Table (Updated)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Relationship to stores (User's selected stores)
    selected_stores = relationship("Store", secondary=user_store_preferences, backref="users")


class Card(Base):
    __tablename__ = "cards"
    name = Column(String, primary_key=True, index=True)


class UserTrackedCards(Base):
    __tablename__ = "user_tracked_cards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_name = Column(String, ForeignKey("cards.name"), nullable=False)

    # Relationship to specifications (one-to-many)
    specifications = relationship("CardSpecification", back_populates="user_card")


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
