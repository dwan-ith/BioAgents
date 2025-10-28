from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, EndSessionContent, StartSessionContent, TextContent, chat_protocol_spec
import requests
import json

agent = Agent(name="DatabaseAgent")

chat_proto = Protocol(spec=chat_protocol_spec)

def fetch_pubchem_data(cid):
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/JSON"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return json.dumps({
                "name": data["PC_Compounds"][0]["props"][0]["value"]["sval"],
                "molecular_weight": data["PC_Compounds"][0]["props"][1]["value"]["fval"]
            })
        else:
            return "{}"
    except:
        return "{}"

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
                cid = query_data.get("cid", "2244")
                data = fetch_pubchem_data(cid)
                response_text = f"PubChem data for CID {cid}: {data}"
            except json.JSONDecodeError:
                response_text = "Invalid query format. Expect JSON with 'cid'."
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