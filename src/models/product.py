"""
Product video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from .base import BaseExtraction


class Product(BaseModel):
    """
    Represents a single product found in a product video.
    
    Example:
        Product(
            name="Nike Air Zoom Pegasus",
            brand="Nike",
            price="₹8,499",
            currency="INR",
            purchase_links=[
                "https://amazon.in/...",
                "https://nike.com/..."
            ],
            product_category="Running Shoes"
        )
    """
    name: str = Field(..., description="Name of the product")
    brand: Optional[str] = Field(None, description="Brand name")
    price: Optional[str] = Field(
        None, 
        description="Price of the product (as displayed, e.g., '₹8,499', '$99.99')"
    )
    currency: Optional[str] = Field(
        None, 
        description="Currency code (e.g., 'INR', 'USD', 'EUR')"
    )
    purchase_links: List[str] = Field(
        default_factory=list, 
        description="Links to purchase the product (Amazon, brand website, etc.)"
    )
    product_category: Optional[str] = Field(
        None, 
        description="Category of the product (e.g., 'Running Shoes', 'Laptop', 'Skincare')"
    )


class ProductCatalog(BaseExtraction):
    """
    Product catalog extracted from a product showcase video reel.
    
    Example:
        ProductCatalog(
            category="product",
            title="Best Running Shoes 2024",
            description="Top running shoes reviewed",
            products=[
                Product(
                    name="Nike Air Zoom Pegasus",
                    brand="Nike",
                    price="₹8,499",
                    purchase_links=["https://amazon.in/..."]
                )
            ]
        )
    """
    category: Literal["product"] = "product"
    products: Optional[List[Product]] = Field(
        default=None, 
        description="List of products found in the video (if extractable)"
    )

