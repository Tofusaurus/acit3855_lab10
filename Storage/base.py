from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String  # Import the necessary SQLAlchemy modules for defining the column


Base = declarative_base()

# Add the trace_id column to the Base class
class BaseModel(Base):
    __abstract__ = True  # This marks this class as abstract and will not create a table for it in the database

    # Define the trace_id column
    trace_id = Column(String(36))  