from supabase_client import supabase
from uuid import uuid4

def create_conversation(user_id, topic):
    conversation_id = str(uuid4())
    supabase.table("conversations").insert({
        "conversation_id": conversation_id,
        "user_id": user_id,
        "conversation_topic": topic
    }).execute()
    return conversation_id

def get_conversations(user_id):
    response = supabase.table("conversations").select("*").eq("user_id", user_id).execute()
    return response.data