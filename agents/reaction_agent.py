from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, EndSessionContent, StartSessionContent, TextContent, chat_protocol_spec
import json
import hyperon as hn
import random

agent = Agent(name="ReactionAgent")

chat_proto = Protocol(spec=chat_protocol_spec)

metta_space = hn.Space()

def load_metta_knowledge():
    global metta_space
    with open('../knowledge/molecules.metta', 'r') as f:
        metta_code = f.read()
    runner = hn.Runner(metta_space)
    runner.run(metta_code)
    print("MeTTa knowledge loaded for ReactionAgent")

load_metta_knowledge()

def query_metta(query_str):
    runner = hn.Runner(metta_space)
    result = runner.run(query_str)
    if result:
        return json.dumps(result.to_dict())
    return "{}"

def simulate_reaction(mol1, mol2):
    interaction_score = random.uniform(0.5, 0.9)
    return f"Interaction between {mol1} and {mol2}: score {interaction_score:.2f}"

def create_text_chat(text, end_session=False):
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    print(f"Received message from {sender}")
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            print(f"Session started with {sender}")
        elif isinstance(item, TextContent):
            print(f"Text message from {sender}: {item.text}")
            try:
                query_data = json.loads(item.text)
                mol1 = query_data.get("mol1", "Aspirin")
                mol2 = query_data.get("mol2", "Caffeine")
                metta_query1 = f"(find ?props (molecule {mol1}))"
                props1 = query_metta(metta_query1)
                metta_query2 = f"(find ?props (molecule {mol2}))"
                props2 = query_metta(metta_query2)
                reaction_result = simulate_reaction(mol1, mol2)
                response_text = f"Reaction: {reaction_result}. Props1: {props1}. Props2: {props2}"
            except json.JSONDecodeError:
                response_text = "Invalid query format. Expect JSON with 'mol1' and 'mol2'."
            response_message = create_text_chat(response_text)
            await ctx.send(sender, response_message)
        elif isinstance(item, EndSessionContent):
            print(f"Session ended with {sender}")
        else:
            print(f"Received unexpected content type from {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    fund_agent_if_low(agent.wallet.address())
    agent.run()