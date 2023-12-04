from sqlalchemy import Column, String, DateTime, Float, Integer  
from base import Base
from datetime import datetime

class InventoryItem(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    item_id = Column(String(250), nullable=False)
    product_name = Column(String)
    storage_date = Column(DateTime)
    stored_by = Column(String)
    weight = Column(Float)
    location = Column(String, nullable=True)  
    date_created = Column(DateTime, default=datetime.now)
    quantity = Column(Integer, nullable=True)  

    def __init__(self, item_id, product_name, storage_date, stored_by, weight, location, date_created, quantity=None):  # Added quantity parameter with a default value of None
        self.item_id = item_id
        self.product_name = product_name
        self.storage_date = storage_date
        self.stored_by = stored_by
        self.weight = weight
        self.location = location
        self.date_created = date_created
        self.quantity = quantity  

    def to_dict(self):
        """ Dictionary Representation of an inventory item """
        dict = {
            'item_id': self.item_id,
            'product_name': self.product_name,
            'storage_date': self.storage_date,
            'stored_by': self.stored_by,
            'weight': self.weight,
            'date_created': self.date_created  
        }

        if self.quantity is not None:  
            dict['quantity'] = self.quantity

        if self.location is not None:
            dict['location'] = self.location

        return dict
