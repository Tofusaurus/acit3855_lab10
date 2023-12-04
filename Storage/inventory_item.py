from sqlalchemy import Column, Integer, String, DateTime
from base import Base
from datetime import datetime

class InventoryItem(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    item_id = Column(String(36), nullable=False)
    product_name = Column(String(250), nullable=False)
    quantity = Column(Integer, nullable=False)
    trace_id = Column(String(36), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)  # Add this line if it's missing
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Assuming you have this column as well

    def to_dict(self):
        """ Dictionary Representation of an inventory item """
        return {
            'id': self.id,
            'item_id': self.item_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'trace_id': self.trace_id,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None
        }
