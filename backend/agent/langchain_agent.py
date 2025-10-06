# LangChain agent that wraps Kleio.ai backend functions as tools
# PURE WRAPPER APPROACH: Tools call existing functions, return data, LLM formats response

from typing import Dict, List, Any, Optional
from datetime import datetime, date
import logging
import json
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from config import settings
from crud.inventory import create_inventory_item, get_user_inventory
from schemas.inventory import InventoryCreate
from utils.pattern_analyzer import generate_shopping_list
from utils.gemini_client import get_gemini_client
from models.inventory import ItemStatus
from database import get_db

logger = logging.getLogger(__name__)


# Agent setup and process_message function

def create_agent(firebase_uid: str, db_session: Session):
    """
    Create LangChain agent for a user with conversation memory.
    
    Args:
        firebase_uid: User's Firebase UID
        db_session: Database session
        
    Returns:
        Configured agent with tools and memory
    """
    
    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    # ============================================================================
    # PURE WRAPPER FUNCTIONS - Just call existing backend functions
    # The LLM will format natural language responses based on the returned data
    # ============================================================================
    
    def add_items_wrapper(items_text: str) -> str:
        """
        Add items to user's inventory from natural language input.
        
        Args:
            items_text: Natural language text like "bought 2kg tomatoes and 1 liter milk"
            
        Returns:
            JSON string with added items details for the LLM to format
        """
        logger.info(f"🔧 TOOL: add_items_wrapper | Input: {items_text}")
        try:
            # Step 1: Parse natural language using Gemini
            gemini = get_gemini_client()
            
            prompt = f"""
Parse this natural language text into structured grocery items:
"{items_text}"

Return ONLY valid JSON array (no markdown):
[
  {{"item_name": "tomatoes", "quantity": 2.0, "unit": "kg", "category": "vegetables"}},
  {{"item_name": "milk", "quantity": 1.0, "unit": "liter", "category": "dairy"}}
]

Categories: vegetables, fruits, dairy, staples, pulses, spices, snacks, beverages, meat, seafood, bakery, frozen, oils, condiments, others
"""
            
            response = gemini.client.models.generate_content(
                model=gemini.MODEL_ID,
                contents=prompt,
                config={"temperature": 0.3, "response_mime_type": "application/json"}
            )
            
            items_data = json.loads(response.text)
            
            if not isinstance(items_data, list) or not items_data:
                return json.dumps({"error": "Could not parse items", "items": []})
            
            # Step 2: Add items using existing CRUD function
            added_items = []
            for item_dict in items_data:
                item = InventoryCreate(**item_dict)
                created_item = create_inventory_item(db_session, firebase_uid, item)
                added_items.append({
                    "name": created_item.item_name,
                    "quantity": float(created_item.quantity),
                    "unit": created_item.unit,
                    "category": created_item.category
                })
                logger.info(f"✅ DB: Added {created_item.item_name}")
            
            # Return structured data for LLM to format
            result = {"success": True, "items_added": added_items, "count": len(added_items)}
            logger.info(f"🔧 RESULT: {len(added_items)} items added")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    def get_shopping_wrapper(urgency: Optional[str] = None) -> str:
        """
        Get smart shopping list based on usage patterns.
        
        Args:
            urgency: Filter by urgency level ('urgent', 'this_week', or None for all)
            
        Returns:
            JSON string with shopping list data for the LLM to format
        """
        logger.info(f"🔧 TOOL: get_shopping_wrapper | Urgency: {urgency}")
        try:
            # Call existing pattern analyzer function
            shopping_list = generate_shopping_list(
                db=db_session,
                firebase_uid=firebase_uid,
                urgency_filter=urgency
            )
            
            # Return raw data for LLM to format naturally
            result = {
                "success": True,
                "urgent": shopping_list["urgent"],
                "this_week": shopping_list["this_week"],
                "later": shopping_list["later"],
                "total_items": len(shopping_list["urgent"]) + len(shopping_list["this_week"]) + len(shopping_list["later"])
            }
            
            logger.info(f"🔧 RESULT: {result['total_items']} items in shopping list")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    def check_ingredients_for_specific_recipe(recipe_name: str) -> str:
        # Checks if a specific recipe is feasible with the user's current inventory.
        logger.info(f"🔧 TOOL: check_specific_recipe_feasibility | Recipe: {recipe_name}")
        try:
            # Step 1: Get recipe ingredients from Gemini
            gemini = get_gemini_client()
            prompt = f"List the essential ingredients for the Indian dish '{recipe_name}'. Return ONLY a JSON array of strings. Example: [ingredient1, ingredient2, ...]."
            response = gemini.client.models.generate_content(
                model=gemini.MODEL_ID,
                contents=prompt,
                config={"temperature": 0.1, "response_mime_type": "application/json"}
            )
            recipe_ingredients = json.loads(response.text)

            # Step 2: Get user's inventory
            inventory_items = get_user_inventory(db_session, firebase_uid, status=ItemStatus.ACTIVE, limit=500)
            inventory_item_names = {item.item_name.lower() for item in inventory_items}

            # Step 3: Compare and find missing ingredients
            have_ingredients = []
            missing_ingredients = []
            for ingredient in recipe_ingredients:
                if ingredient.lower() in inventory_item_names:
                    have_ingredients.append(ingredient)
                else:
                    missing_ingredients.append(ingredient)

            result = {
                "success": True,
                "recipe_name": recipe_name,
                "have_ingredients": have_ingredients,
                "missing_ingredients": missing_ingredients,
                "feasible": len(missing_ingredients) == 0
            }
            return json.dumps(result)

        except Exception as e:
            logger.error(f"❌ Error in check_specific_recipe_feasibility: {e}")
            return json.dumps({"error": str(e), "success": False})

    def suggest_recipe_from_inventory(preferences: str = "") -> str:
        # Check if a recipe is feasible with current inventory items.
        logger.info(f"🔧 TOOL: check_recipe_feasibility | Preferences: {preferences}")
        try:
            inventory_items = get_user_inventory(
                db_session,
                firebase_uid,
                status=ItemStatus.ACTIVE,
                limit=500
            )
            if not inventory_items:
                return json.dumps({
                    "success": False,
                    "error": "Empty inventory",
                    "message": "No items in inventory to generate recipe"
                })
            available_items = [f"{item.item_name} ({item.quantity}{item.unit})" for item in inventory_items]
            filters = {"cooking_time": 45, "meal_type": "any", "cuisine": "Indian"}
            prefs_lower = preferences.lower()
            if "quick" in prefs_lower or "fast" in prefs_lower or "30" in prefs_lower:
                filters["cooking_time"] = 30
            if "lunch" in prefs_lower:
                filters["meal_type"] = "lunch"
            elif "dinner" in prefs_lower:
                filters["meal_type"] = "dinner"
            elif "breakfast" in prefs_lower:
                filters["meal_type"] = "breakfast"
            gemini = get_gemini_client()
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            recipe = loop.run_until_complete(gemini.generate_recipe(
                available_items=available_items,
                dietary_preferences={
                    "vegetarian": "vegetarian" in prefs_lower or "veg" in prefs_lower,
                    "vegan": "vegan" in prefs_lower,
                },
                filters=filters
            ))
            result = {
                "success": True,
                "recipe_name": recipe.get("recipe_name"),
                "description": recipe.get("description"),
                "cooking_time": recipe.get("cooking_time_minutes"),
                "servings": recipe.get("servings"),
                "difficulty": recipe.get("difficulty"),
                "ingredients": recipe.get("ingredients", []),
                "available_count": sum(1 for ing in recipe.get("ingredients", []) if ing.get("available")),
                "missing_count": sum(1 for ing in recipe.get("ingredients", []) if not ing.get("available")),
                "feasible": sum(1 for ing in recipe.get("ingredients", []) if ing.get("available")) >= len(recipe.get("ingredients", [])) * 0.7
            }
            logger.info(f"🔧 RESULT: Recipe '{result['recipe_name']}' - {result['available_count']}/{len(recipe.get('ingredients', []))} items available")
            return json.dumps(result)
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return json.dumps({"error": str(e), "success": False})


    
    def query_inventory_wrapper(category: Optional[str] = None) -> str:
        """
        Query user's current inventory items.
        
        Args:
            category: Optional category filter (e.g., 'vegetables', 'dairy')
            
        Returns:
            JSON string with inventory data for the LLM to format
        """
        logger.info(f"🔧 TOOL: query_inventory_wrapper | Category: {category}")
        try:
            # Call existing CRUD function
            inventory_items = get_user_inventory(
                db_session,
                firebase_uid,
                status=ItemStatus.ACTIVE,
                category=category,
                limit=100
            )
            
            if not inventory_items:
                return json.dumps({
                    "success": True,
                    "items": [],
                    "total": 0,
                    "message": f"No {category} items found" if category else "Inventory is empty"
                })
            
            # Convert to JSON-serializable format
            items_data = []
            for item in inventory_items:
                expiry_info = None
                if item.expiry_date:
                    days_left = (item.expiry_date - date.today()).days
                    expiry_info = {
                        "date": item.expiry_date.isoformat(),
                        "days_left": days_left,
                        "status": "urgent" if days_left <= 3 else "soon" if days_left <= 7 else "ok"
                    }
                
                items_data.append({
                    "name": item.item_name,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "category": item.category,
                    "expiry": expiry_info,
                    "added_date": item.added_date.isoformat()
                })
            
            # Group by category
            by_category = {}
            for item_data in items_data:
                cat = item_data["category"]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(item_data)
            
            result = {
                "success": True,
                "items": items_data,
                "by_category": by_category,
                "total": len(items_data)
            }
            
            logger.info(f"🔧 RESULT: {len(items_data)} items in inventory")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    # ============================================================================
    # Register tools with LangChain
    # ============================================================================
    from langchain.tools import StructuredTool
    
    tools = [
        StructuredTool.from_function(
            func=add_items_wrapper,
            name="add_inventory_items",
            description="Add items to inventory from natural language (e.g., 'bought 2kg tomatoes and milk'). Returns JSON with added items that you MUST format into a natural response."
        ),
        StructuredTool.from_function(
            func=query_inventory_wrapper,
            name="query_inventory",
            description="Query user's current inventory items. Optional category filter. Returns JSON with items data that you MUST format into a natural response."
        ),
        StructuredTool.from_function(
            func=get_shopping_wrapper,
            name="get_shopping_list",
            description="Generate smart shopping list based on usage patterns. Returns JSON with urgent/this_week/later items that you MUST format into a natural response."
        ),
        StructuredTool.from_function(
            func=suggest_recipe_from_inventory,
            name="suggest_recipe_from_inventory",
            description="Suggest a recipe from current inventory. Generates full recipe with ingredients marked as available/missing. Returns JSON that you MUST format into a helpful natural response."
        ),
        StructuredTool.from_function(
            func=check_ingredients_for_specific_recipe,
            name="check_ingredients_for_specific_recipe",
            description="Check if a specific recipe is feasible with current inventory. Returns JSON with ingredients that are available/missing. Returns JSON that you MUST format into a helpful natural response."
        ),
    ]
    
    # ============================================================================
    # System Prompt - Define agent behavior
    # ============================================================================
    system_message = f"""You are Kleio, a friendly household inventory assistant for Indian families.

USER ID: {firebase_uid}

HOW YOU WORK:
1. Tools return JSON data with structured information
2. You MUST call the appropriate tool for every user request
3. You MUST format the JSON data into natural, friendly responses
4. You NEVER make up data - only use what tools return
5. When user asks for a recipe, you should clarify the preferences (e.g. vegetarian, vegan, quick, lunch, dinner, breakfast)
6. When you return a response to user, make sure to follow a warm tone and make the user feel like you are a real person.
7. Do not just respond with the tool call, always format the response in a natural way like a real person would.
8. If the user asks anything apart from the tools, you should respond with a friendly and helpful message and ask them to visit the website kleio.ai to get more information.

AVAILABLE TOOLS & WHEN TO USE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 add_inventory_items(items_text)
   When: User says they bought/added items
   Returns: JSON with added items
   You format as: "✅ Added [items] to your inventory!"

📦 query_inventory(category)
   When: User asks what they have
   Returns: JSON with inventory items grouped by category
   You format as: Natural list organized by category with quantities

🛒 get_shopping_list(urgency)
   When: User asks what to buy
   Returns: JSON with urgent/this_week/later items
   You format as: Organized shopping list with urgency levels

🍳 suggest_recipe_from_inventory(preferences)
   When: User wants recipe suggestions
   Returns: JSON with recipe details and ingredient availability
   You format as: Recipe summary with what they have vs need to buy

🍳 check_ingredients_for_specific_recipe(recipe_name)
   When: User wants to check ingredients for a specific recipe
   Returns: JSON with ingredients that are available/missing
   You format as: Recipe summary with what they have vs need to buy

RESPONSE STYLE FOR TELEGRAM:
✅ Friendly and conversational (but not overly chatty)
✅ Use emojis appropriately: ✅ ❌ 🔴 🟡 🟢 📦 🛒 🍳 ☀️ 🌙
✅ Use *bold* for emphasis (e.g., *recipe names*, *important items*)
✅ Use _italic_ for secondary emphasis or notes
✅ Indian context: kg, liters, INR, common Indian items
✅ Clear and actionable information
✅ Use natural bullet points with • or numbered lists
✅ Keep responses concise but complete

❌ Never say "I'll try" or "let me" - just call the tool and report results
❌ Never apologize for non-existent errors
❌ Never make up data
❌ Don't use excessive formatting - keep it clean

EXAMPLES:
User: "bought 2kg tomatoes and milk"
You: Call add_inventory_items("bought 2kg tomatoes and milk") → Format JSON as natural response

User: "what vegetables do I have?"
You: Call query_inventory("vegetables") → Format JSON showing vegetables with quantities

User: "what should I buy this week?"
You: Call get_shopping_list("this_week") → Format JSON as organized shopping list

User: "can I make dinner with what I have?"
You: Call check_recipe_feasibility("dinner") → Format JSON showing recipe feasibility
"""
    
    # Create agent with memory
    memory = MemorySaver()
    agent = create_react_agent(
        llm,
        tools,
        state_modifier=system_message,
        checkpointer=memory
    )
    
    return agent


async def process_message(firebase_uid: str, message: str, thread_id: str = "default") -> str:
    """
    Process user message through LangChain agent.
    
    Args:
        firebase_uid: User's Firebase UID
        message: User's message
        thread_id: Conversation thread ID for memory (default: "default")
        
    Returns:
        Agent's response as string
        
    Example:
        response = await process_message("user123", "I bought 2kg tomatoes and milk", "chat-1")
    """
    try:
        logger.info(f"Processing message for {firebase_uid}: {message}")
        
        # Get database session
        db = next(get_db())
        
        # Create agent with bound context
        agent = create_agent(firebase_uid, db)
        
        # Invoke agent
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        response = agent.invoke(
            {"messages": [("user", message)]},
            config=config
        )
        
        # Extract final response
        messages = response.get("messages", [])
        logger.info(f"📨 Agent returned {len(messages)} messages")
        
        if messages:
            final_message = messages[-1]
            logger.info(f"📨 Final message type: {type(final_message).__name__}")
            if hasattr(final_message, "content"):
                logger.info(f"📨 Final response: {final_message.content[:200]}...")
                return final_message.content
            return str(final_message)
        
        return "I'm sorry, I couldn't process that request. Please try again."
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error: {str(e)}"


# Synchronous wrapper for non-async contexts
def process_message_sync(firebase_uid: str, message: str, thread_id: str = "default") -> str:
    """
    Synchronous wrapper for process_message.
    
    IMPORTANT: Use this ONLY in non-async contexts (scripts, CLI, sync code).
    For FastAPI async endpoints, use process_message() directly with await.
    
    This function creates its own event loop, which conflicts with existing loops.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(process_message(firebase_uid, message, thread_id))

