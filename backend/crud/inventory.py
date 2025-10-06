# CRUD operations for Inventory model


from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime
import logging

from models.inventory import Inventory, ItemStatus
from models.consumption_log import ConsumptionLog
from schemas.inventory import InventoryCreate, InventoryUpdate, InventoryMarkUsed
from crud.purchase_log import create_purchase_log

logger = logging.getLogger(__name__)


def create_inventory_item(
    db: Session, 
    firebase_uid: str, 
    item_data: InventoryCreate
) -> Inventory:
    """
    Create a new inventory item OR update existing one
    
    If an active item with the same name already exists, updates the quantity.
    Otherwise, creates a new item.
    
    Args:
        db: Database session
        firebase_uid: User's Firebase UID
        item_data: Inventory item data
        
    Returns:
        Inventory: Created or updated inventory item
    """
    # Check if item already exists (active status, same name)
    existing_item = db.query(Inventory).filter(
        and_(
            Inventory.firebase_uid == firebase_uid,
            Inventory.item_name.ilike(item_data.item_name),  # Case-insensitive match
            Inventory.status == ItemStatus.ACTIVE
        )
    ).first()
    
    if existing_item:
        # Update existing item - add quantities
        existing_item.quantity += item_data.quantity
        
        # Update expiry date if new one is provided and is sooner
        if item_data.expiry_date:
            if not existing_item.expiry_date or item_data.expiry_date < existing_item.expiry_date:
                existing_item.expiry_date = item_data.expiry_date
        
        db.commit()
        db.refresh(existing_item)
        
        # Log this purchase for pattern analysis
        create_purchase_log(
            db=db,
            firebase_uid=firebase_uid,
            item_name=existing_item.item_name,
            category=existing_item.category,
            quantity=float(item_data.quantity),
            unit=existing_item.unit,
            inventory_id=existing_item.id
        )
        
        logger.info(f"Updated inventory item: {existing_item.item_name} (new qty: {existing_item.quantity}{existing_item.unit}) for user {firebase_uid}")
        return existing_item
    else:
        # Create new item
        item_dict = item_data.model_dump()
        item_dict.pop("estimated_shelf_life_days", None)
        new_item = Inventory(
            firebase_uid=firebase_uid,
            **item_dict
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # Log this purchase for pattern analysis
        create_purchase_log(
            db=db,
            firebase_uid=firebase_uid,
            item_name=new_item.item_name,
            category=new_item.category,
            quantity=float(new_item.quantity),
            unit=new_item.unit,
            inventory_id=new_item.id
        )
        
        logger.info(f"Created inventory item: {new_item.item_name} for user {firebase_uid}")
        return new_item


def get_user_inventory(
    db: Session,
    firebase_uid: str,
    status: Optional[ItemStatus] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Inventory]:
    """
    Get user's inventory items with optional filtering
    
    Args:
        db: Database session
        firebase_uid: User's Firebase UID
        status: Filter by status (optional)
        category: Filter by category (optional)
        limit: Maximum number of items to return
        offset: Number of items to skip (for pagination)
        
    Returns:
        List[Inventory]: List of inventory items
    """
    query = db.query(Inventory).filter(Inventory.firebase_uid == firebase_uid)
    
    # Apply filters
    if status:
        query = query.filter(Inventory.status == status)
    
    if category:
        query = query.filter(Inventory.category == category)
    
    # Order by most recently added first
    query = query.order_by(Inventory.created_at.desc())
    
    # Pagination
    query = query.limit(limit).offset(offset)
    
    return query.all()


def get_inventory_item(
    db: Session,
    item_id: int,
    firebase_uid: str
) -> Optional[Inventory]:
    """
    Get a specific inventory item
    
    Args:
        db: Database session
        item_id: Inventory item ID
        firebase_uid: User's Firebase UID (for ownership verification)
        
    Returns:
        Inventory | None: Inventory item if found and owned by user
    """
    return db.query(Inventory).filter(
        and_(
            Inventory.id == item_id,
            Inventory.firebase_uid == firebase_uid
        )
    ).first()


def update_inventory_item(
    db: Session,
    item_id: int,
    firebase_uid: str,
    update_data: InventoryUpdate
) -> Optional[Inventory]:
    """
    Update an inventory item
    
    Args:
        db: Database session
        item_id: Inventory item ID
        firebase_uid: User's Firebase UID
        update_data: Updated data
        
    Returns:
        Inventory | None: Updated inventory item if found
    """
    item = get_inventory_item(db, item_id, firebase_uid)
    
    if not item:
        return None
    
    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    logger.info(f"Updated inventory item {item_id}")
    return item


def delete_inventory_item(
    db: Session,
    item_id: int,
    firebase_uid: str
) -> bool:
    """
    Soft delete an inventory item (mark as consumed)
    
    Args:
        db: Database session
        item_id: Inventory item ID
        firebase_uid: User's Firebase UID
        
    Returns:
        bool: True if deleted, False if not found
    """
    item = get_inventory_item(db, item_id, firebase_uid)
    
    if not item:
        return False
    
    # Soft delete: change status to consumed
    item.status = ItemStatus.CONSUMED
    db.commit()
    logger.info(f"Soft deleted inventory item {item_id}")
    return True


def mark_item_as_used(
    db: Session,
    item_id: int,
    firebase_uid: str,
    used_data: InventoryMarkUsed
) -> Optional[Inventory]:
    """
    Mark an item as used/consumed and log it for pattern analysis
    
    Args:
        db: Database session
        item_id: Inventory item ID
        firebase_uid: User's Firebase UID
        used_data: Amount used (optional, defaults to all)
        
    Returns:
        Inventory | None: Updated inventory item if found
    """
    item = get_inventory_item(db, item_id, firebase_uid)
    
    if not item:
        return None
    
    # Calculate quantity consumed
    quantity_used = used_data.quantity_used if used_data.quantity_used else item.quantity
    
    # Calculate days lasted
    days_lasted = (date.today() - item.added_date).days
    if days_lasted < 1:
        days_lasted = 1  # Minimum 1 day
    
    # Log consumption for pattern analysis
    consumption_log = ConsumptionLog(
        firebase_uid=firebase_uid,
        item_name=item.item_name,
        category=item.category,
        quantity_consumed=quantity_used,
        unit=item.unit,
        consumed_date=date.today(),
        added_date=item.added_date,
        days_lasted=days_lasted,
        inventory_id=item_id
    )
    
    db.add(consumption_log)
    
    # Update inventory item
    if used_data.quantity_used and used_data.quantity_used < item.quantity:
        # Partial consumption - reduce quantity
        item.quantity -= used_data.quantity_used
    else:
        # Full consumption - mark as consumed
        item.status = ItemStatus.CONSUMED
        item.quantity = 0
    
    db.commit()
    db.refresh(item)
    logger.info(f"Marked item {item_id} as used: {quantity_used} {item.unit}")
    return item


def get_common_items(
    db: Session,
    firebase_uid: str,
    search_query: Optional[str] = None,
    limit: int = 10
) -> List[str]:
    """
    Get common/frequent items for autocomplete
    
    Args:
        db: Database session
        firebase_uid: User's Firebase UID
        search_query: Search term (optional)
        limit: Maximum number of suggestions
        
    Returns:
        List[str]: List of item names
    """
    query = db.query(Inventory.item_name).filter(
        Inventory.firebase_uid == firebase_uid
    ).distinct()
    
    if search_query:
        query = query.filter(Inventory.item_name.ilike(f"%{search_query}%"))
    
    query = query.limit(limit)
    
    return [item[0] for item in query.all()]

