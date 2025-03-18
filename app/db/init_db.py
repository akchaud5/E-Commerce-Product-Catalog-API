import asyncio
import logging
from bson import ObjectId

from app.db.mongodb import database
from app.services import user_service, category_service, product_service
from app.models.user import UserCreate
from app.models.category import CategoryCreate
from app.models.product import ProductCreate


async def init_db():
    logger = logging.getLogger("app.init_db")
    logger.info("Creating initial data")
    
    # Create admin user if it doesn't exist
    admin_user = await user_service.get_user_by_email("admin@example.com")
    if not admin_user:
        logger.info("Creating admin user")
        admin_data = UserCreate(
            email="admin@example.com",
            username="admin",
            password="admin123"  # In production, use a strong password
        )
        admin_user = await user_service.create_user(admin_data)
        
        # Make the user an admin
        await database.users.update_one(
            {"_id": admin_user.id},
            {"$set": {"is_admin": True}}
        )
        logger.info(f"Admin user created with ID: {admin_user.id}")
    
    # Create initial categories if they don't exist
    categories = [
        {"name": "Electronics", "description": "Electronic devices and gadgets"},
        {"name": "Clothing", "description": "Apparel and fashion items"},
        {"name": "Books", "description": "Books and publications"},
        {"name": "Home & Kitchen", "description": "Products for home and kitchen"},
        {"name": "Beauty & Personal Care", "description": "Beauty products and personal care items"}
    ]
    
    category_ids = {}
    
    for category_data in categories:
        existing = await category_service.get_category_by_name(category_data["name"])
        if not existing:
            logger.info(f"Creating category: {category_data['name']}")
            category = await category_service.create_category(
                CategoryCreate(**category_data)
            )
            category_ids[category_data["name"]] = category.id
        else:
            category_ids[category_data["name"]] = existing.id
    
    # Create initial products if they don't exist
    products = [
        {
            "name": "Smartphone X",
            "description": "Latest smartphone with advanced features",
            "price": 699.99,
            "stock": 50,
            "category_id": str(category_ids["Electronics"]),
            "image_url": "https://example.com/smartphone.jpg",
            "tags": ["smartphone", "electronics", "mobile"]
        },
        {
            "name": "Laptop Pro",
            "description": "Professional laptop for work and entertainment",
            "price": 1299.99,
            "stock": 30,
            "category_id": str(category_ids["Electronics"]),
            "image_url": "https://example.com/laptop.jpg",
            "tags": ["laptop", "computer", "electronics"]
        },
        {
            "name": "Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt",
            "price": 19.99,
            "stock": 100,
            "category_id": str(category_ids["Clothing"]),
            "image_url": "https://example.com/tshirt.jpg",
            "tags": ["clothing", "t-shirt", "fashion"]
        },
        {
            "name": "Denim Jeans",
            "description": "Classic denim jeans",
            "price": 49.99,
            "stock": 80,
            "category_id": str(category_ids["Clothing"]),
            "image_url": "https://example.com/jeans.jpg",
            "tags": ["clothing", "jeans", "fashion"]
        },
        {
            "name": "Programming Guide",
            "description": "Comprehensive programming guide",
            "price": 34.99,
            "stock": 40,
            "category_id": str(category_ids["Books"]),
            "image_url": "https://example.com/programming-book.jpg",
            "tags": ["book", "programming", "learning"]
        },
        {
            "name": "Coffee Maker",
            "description": "Automatic coffee maker for home",
            "price": 89.99,
            "stock": 25,
            "category_id": str(category_ids["Home & Kitchen"]),
            "image_url": "https://example.com/coffee-maker.jpg",
            "tags": ["kitchen", "appliance", "coffee"]
        },
        {
            "name": "Facial Cleanser",
            "description": "Gentle facial cleanser for all skin types",
            "price": 14.99,
            "stock": 60,
            "category_id": str(category_ids["Beauty & Personal Care"]),
            "image_url": "https://example.com/cleanser.jpg",
            "tags": ["beauty", "skincare", "facial"]
        }
    ]
    
    for product_data in products:
        # Check if product with same name exists
        existing_products = await product_service.get_all_products(
            filter_params={"name": product_data["name"]}
        )
        
        if not existing_products:
            logger.info(f"Creating product: {product_data['name']}")
            await product_service.create_product(
                ProductCreate(**product_data)
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())