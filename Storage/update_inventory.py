from sqlalchemy import Column, String, DateTime, Float, Integer
from base import Base
from datetime import datetime

class UpdateInventoryItem(Base):
    """ Update Inventory Item Class """

    __tablename__ = "update_inventory"

    id = Column(Integer, primary_key=True)
    item_id = Column(String(250), nullable=False)  
    product_name = Column(String(250), nullable=True)  
    storage_date = Column(DateTime, nullable=True)
    stored_by = Column(String(250), nullable=True)
    weight = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    location = Column(String(250), nullable=True)
    trace_id = Column(String(36), nullable=False)  # Add this line
    date_updated = Column(DateTime, nullable=False) 

    def __init__(self, item_id, product_name, storage_date, stored_by, weight, location, trace_id, date_updated, quantity=None):
        """ Initializes an update inventory item record """
        self.item_id = item_id
        self.product_name = product_name
        self.storage_date = storage_date
        self.stored_by = stored_by
        self.weight = weight
        self.quantity = quantity
        self.location = location
        self.trace_id = trace_id  # Add this line
        self.date_updated = date_updated 

    def to_dict(self):
        """ Dictionary Representation of an update inventory item record """
        
        dict = {
            'item_id': self.item_id,
            'trace_id': self.trace_id  # Add this line
        }

        if self.product_name is not None:
            dict['product_name'] = self.product_name

        if self.storage_date is not None:
            dict['storage_date'] = self.storage_date

        if self.stored_by is not None:
            dict['stored_by'] = self.stored_by

        if self.weight is not None:
            dict['weight'] = self.weight

        if self.quantity is not None:
            dict['quantity'] = self.quantity

        if self.location is not None:
            dict['location'] = self.location

        return dict
