from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    selected_stores = Column(Text)  # JSON list of stores

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    set_code = Column(String)
    collector_id = Column(String)
    finish = Column(String)
    image_url = Column(Text)  # Store the URL instead of the actual image

class TrackedCard(Base):
    __tablename__ = "tracked_cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))

    user = relationship("User")
    card = relationship("Card")

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
