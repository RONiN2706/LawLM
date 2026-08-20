from conversations import create_conversation, get_conversations
from save_messages import save_message, get_messages
from api_usage import save_api_usage

user_id = "8a4e62f9-22be-409a-b433-17a1c5a3f5e5"

conversation_id = create_conversation(
    user_id,
    "Test Conversation"
)

message_id = save_message(
    conversation_id,
    "Test user question",
    "Test AI answer"
)


print("Conversation:", conversation_id)
print("Message:", message_id)

messages = get_messages(conversation_id)
print("Messages:", messages)

usage_id = save_api_usage(
    conversation_id,
    "test_model",
    100,
    50,
    150
)
print("API Usage:", usage_id)