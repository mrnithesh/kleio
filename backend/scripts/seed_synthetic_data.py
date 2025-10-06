# Seed synthetic data for a specific Firebase UID
# Usage:
#   python backend/scripts/seed_synthetic_data.py --uid <FIREBASE_UID> [--weeks 4] [--months 6] [--reset]
#  python scripts/seed_synthetic_data.py --uid LONo1WRY7XTbLSmx8uy4jC5YGo22 --reset --weeks 4 --months 6
#  python scripts/seed_synthetic_data.py --uid ol0ce2Zvy1bvA6aYVkN4ywjdOHB2 --reset --weeks 4 --months 6
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import argparse
import logging

from sqlalchemy.orm import Session

from database import SessionLocal
from models.user import User
from models.inventory import Inventory, ItemStatus
from models.purchase_log import PurchaseLog
from models.consumption_log import ConsumptionLog
from utils.pattern_analyzer import analyze_item_pattern, generate_shopping_list
from crud.pattern_analysis import analyze_and_save_user_patterns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upsert_user(db: Session, firebase_uid: str):
    # Create user if not exists
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user:
        logger.info(f"User exists: {firebase_uid}")
        return user
    user = User(
        firebase_uid=firebase_uid,
        household_size=4,
        language_preference="en",
        region="south"
    )
    db.add(user)
    db.commit()
    logger.info(f"✅ Created user: {firebase_uid}")
    return user


def reset_user_data(db: Session, firebase_uid: str):
    # Delete purchase, consumption, inventory for this user
    from models.shopping_prediction import ShoppingPrediction
    deleted_p = db.query(PurchaseLog).filter(PurchaseLog.firebase_uid == firebase_uid).delete()
    deleted_c = db.query(ConsumptionLog).filter(ConsumptionLog.firebase_uid == firebase_uid).delete()
    deleted_i = db.query(Inventory).filter(Inventory.firebase_uid == firebase_uid).delete()
    deleted_pred = db.query(ShoppingPrediction).filter(ShoppingPrediction.firebase_uid == firebase_uid).delete()
    db.commit()
    logger.info(f"🧹 Reset data for {firebase_uid}: purchases={deleted_p}, consumptions={deleted_c}, inventory={deleted_i}, predictions={deleted_pred}")


def seed_milk(db: Session, firebase_uid: str, weeks: int = 4):
    # Buy 2L every 3 days, consume in 2 days
    item_name = "milk"
    category = "dairy"
    for day in range(0, weeks * 7, 3):
        purchase_date = date.today() - timedelta(days=(weeks * 7) - day)
        consume_date = purchase_date + timedelta(days=2)
        db.add(PurchaseLog(
            firebase_uid=firebase_uid,
            item_name=item_name,
            category=category,
            quantity_purchased=2.0,
            unit="liters",
            purchase_date=purchase_date
        ))
        db.add(ConsumptionLog(
            firebase_uid=firebase_uid,
            item_name=item_name,
            category=category,
            quantity_consumed=2.0,
            unit="liters",
            consumed_date=consume_date,
            added_date=purchase_date,
            days_lasted=2
        ))
    db.add(Inventory(
        firebase_uid=firebase_uid,
        item_name=item_name,
        category=category,
        quantity=0.5,
        unit="liters",
        status=ItemStatus.ACTIVE
    ))
    db.commit()
    logger.info(f"✅ Seeded milk for {firebase_uid} ({weeks} weeks)")


def seed_rice(db: Session, firebase_uid: str, months: int = 6):
    # Buy 5kg monthly, lasts 25 days, 2kg left now
    item_name = "rice"
    category = "staples"
    for month in range(months):
        purchase_date = date.today() - timedelta(days=(months - month) * 30)
        consume_date = purchase_date + timedelta(days=25)
        db.add(PurchaseLog(
            firebase_uid=firebase_uid,
            item_name=item_name,
            category=category,
            quantity_purchased=5.0,
            unit="kg",
            purchase_date=purchase_date
        ))
        db.add(ConsumptionLog(
            firebase_uid=firebase_uid,
            item_name=item_name,
            category=category,
            quantity_consumed=5.0,
            unit="kg",
            consumed_date=consume_date,
            added_date=purchase_date,
            days_lasted=25
        ))
    db.add(Inventory(
        firebase_uid=firebase_uid,
        item_name=item_name,
        category=category,
        quantity=2.0,
        unit="kg",
        status=ItemStatus.ACTIVE
    ))
    db.commit()
    logger.info(f"✅ Seeded rice for {firebase_uid} ({months} months)")


def seed_vegetables(db: Session, firebase_uid: str):
    # Tomatoes, onions, potatoes – every 2 days for 3 weeks, lasts 1 day, small current stock
    for veg in ["tomatoes", "onions", "potatoes"]:
        for day in range(0, 21, 2):
            purchase_date = date.today() - timedelta(days=21 - day)
            consume_date = purchase_date + timedelta(days=1)
            db.add(PurchaseLog(
                firebase_uid=firebase_uid,
                item_name=veg,
                category="vegetables",
                quantity_purchased=0.5,
                unit="kg",
                purchase_date=purchase_date
            ))
            db.add(ConsumptionLog(
                firebase_uid=firebase_uid,
                item_name=veg,
                category="vegetables",
                quantity_consumed=0.5,
                unit="kg",
                consumed_date=consume_date,
                added_date=purchase_date,
                days_lasted=1
            ))
        db.add(Inventory(
            firebase_uid=firebase_uid,
            item_name=veg,
            category="vegetables",
            quantity=0.2,
            unit="kg",
            status=ItemStatus.ACTIVE
        ))
    db.commit()
    logger.info(f"✅ Seeded vegetables for {firebase_uid}")


def seed_oil_and_dal(db: Session, firebase_uid: str):
    # Seed cooking oil (long lasting) and toor dal (pulses)
    db.add(PurchaseLog(
        firebase_uid=firebase_uid,
        item_name="cooking oil",
        category="oils",
        quantity_purchased=1.0,
        unit="liters",
        purchase_date=date.today() - timedelta(days=20)
    ))
    db.add(Inventory(
        firebase_uid=firebase_uid,
        item_name="cooking oil",
        category="oils",
        quantity=0.4,
        unit="liters",
        status=ItemStatus.ACTIVE
    ))
    
    for day in [60, 30, 5]:
        db.add(PurchaseLog(
            firebase_uid=firebase_uid,
            item_name="toor dal",
            category="pulses",
            quantity_purchased=1.0,
            unit="kg",
            purchase_date=date.today() - timedelta(days=day)
        ))
    db.add(ConsumptionLog(
        firebase_uid=firebase_uid,
        item_name="toor dal",
        category="pulses",
        quantity_consumed=1.0,
        unit="kg",
        consumed_date=date.today() - timedelta(days=2),
        added_date=date.today() - timedelta(days=30),
        days_lasted=28
    ))
    db.add(Inventory(
        firebase_uid=firebase_uid,
        item_name="toor dal",
        category="pulses",
        quantity=0.3,
        unit="kg",
        status=ItemStatus.ACTIVE
    ))
    db.commit()
    logger.info(f"✅ Seeded oil and dal for {firebase_uid}")


def print_shopping_list(db: Session, firebase_uid: str):
    # Generate and print grouped shopping list
    sl = generate_shopping_list(db, firebase_uid)
    total = len(sl["urgent"]) + len(sl["this_week"]) + len(sl["later"])
    logger.info("\n🛒 SHOPPING LIST PREVIEW")
    logger.info("=" * 60)
    logger.info(f"Total items: {total}")
    if sl["urgent"]:
        logger.info("\n🚨 URGENT:")
        for it in sl["urgent"]:
            logger.info(f"  - {it['item_name']}: {it['suggested_quantity']}{it['unit']} ({it['reason']}, {it['confidence']})")
    if sl["this_week"]:
        logger.info("\n📅 THIS WEEK:")
        for it in sl["this_week"]:
            logger.info(f"  - {it['item_name']}: {it['suggested_quantity']}{it['unit']} ({it['reason']}, {it['confidence']})")
    if sl["later"]:
        logger.info("\n✅ LATER:")
        for it in sl["later"]:
            logger.info(f"  - {it['item_name']}: {it['suggested_quantity']}{it['unit']} ({it['reason']})")


def main():
    parser = argparse.ArgumentParser(description="Seed synthetic data for a Firebase UID")
    parser.add_argument("--uid", required=True, help="Firebase UID to seed data for")
    parser.add_argument("--weeks", type=int, default=4, help="Weeks of milk data")
    parser.add_argument("--months", type=int, default=6, help="Months of rice data")
    parser.add_argument("--reset", action="store_true", help="Reset existing data for this UID before seeding")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        upsert_user(db, args.uid)
        if args.reset:
            reset_user_data(db, args.uid)
        seed_milk(db, args.uid, weeks=args.weeks)
        seed_rice(db, args.uid, months=args.months)
        seed_vegetables(db, args.uid)
        seed_oil_and_dal(db, args.uid)

        # Trigger pattern analysis and save predictions
        analyzed = analyze_and_save_user_patterns(db, args.uid)
        logger.info(f"\n✅ Pattern analysis complete. Predictions saved: {analyzed}")

        # Print quick preview
        print_shopping_list(db, args.uid)

        logger.info("\n🎉 Seeding complete!")
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

