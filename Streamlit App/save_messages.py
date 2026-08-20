from supabase_client import supabase
from uuid import uuid4

def save_message(conversation_id, prompt, answer):
    message_id = str(uuid4())
    supabase.table("messages").insert({
        "message_id": message_id,
        "conversation_id": conversation_id,
        "prompt": prompt,
        "answer": answer
    }).execute()
    return message_id

def get_messages(conversation_id):
    response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).execute()
    return response.data