from supabase_client import supabase
from uuid import uuid4

def save_api_usage(conversation_id, ai_model, input_token, output_token, total_token):
    usage_id = str(uuid4())
    supabase.table("api_usage").insert({
        "usage_id": usage_id,
        "ai_model": ai_model,
        "input_token": input_token,
        "output_token": output_token,
        "total_token": total_token,
        "conversation_id": conversation_id
    }).execute()
    return usage_id