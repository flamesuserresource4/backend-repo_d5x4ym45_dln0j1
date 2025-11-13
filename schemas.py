"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class Generation(BaseModel):
    """
    Content generations created by the AI workflow
    Collection name: "generation"
    """
    prompt: str = Field(..., description="User prompt or brief")
    tone: str = Field(..., description="Selected tone, e.g., Professional, Playful")
    sentiment: str = Field(..., description="Selected sentiment, e.g., Positive, Neutral, Urgent")
    length: str = Field('Medium', description="Output length: Short | Medium | Long")
    creativity: float = Field(0.35, ge=0.0, le=1.0, description="Creativity/temperature 0–1")
    variants: int = Field(1, ge=1, le=5, description="How many variants to generate")
    result: Optional[str] = Field(None, description="Generated content text")
