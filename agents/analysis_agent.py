from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, EndSessionContent, StartSessionContent, TextContent, chat_protocol_spec
import json
import hyperon as hn
import statistics

agent = Agent(name="AnalysisAgent")

chat_proto = Protocol(spec=chat_protocol_spec)

metta_space = hn.Space()

def load_metta_knowledge():
    global metta_space
    with open('../knowledge/molecules.metta', 'r') as f:
        metta_code = f.read()
    runner = hn.Runner(metta_space)
    runner.run(metta_code)
    print("MeTTa knowledge loaded for AnalysisAgent")

load_metta_knowledge()

def query_metta(query_str):
    runner = hn.Runner(metta_space)
    result = runner.run(query_str)
    if result:
        return json.dumps(result.to_dict())
    return "{}"

def analyze_results(results_json):
    try:
        results = json.loads(results_json)
        scores = [float(r.get("toxicity_score", 1.0)) for r in results]
        avg_score = statistics.mean(scores)
        ranked = sorted(results, key=lambda x: float(x.get("toxicity_score", 1.0)))
        return {"average_score": avg_score, "ranked": ranked}
    except:
        return {"error": "Analysis failed"}

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
            analysis = analyze_results(item.text)
            response_text = json.dumps(analysis)
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