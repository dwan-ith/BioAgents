from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

AGENT_ADDRESSES = {
    "research": "agent1qresearchaddress",
    "analysis": "agent1qanalysisaddress"
}

def send_to_agent(agent_name, message):
    try:
        url = f"http://agentverse/api/send/{AGENT_ADDRESSES[agent_name]}"
        payload = {"content": [{"type": "text", "text": message}]}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error sending to {agent_name}: {response.status_code}")
            return {"error": "Failed to send message"}
    except Exception as e:
        print(f"Exception in send_to_agent: {str(e)}")
        return {"error": str(e)}

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    research_response = send_to_agent("research", query)
    if "error" in research_response:
        return jsonify(research_response), 500
    
    processed_query = research_response.get("response", query)
    analysis_response = send_to_agent("analysis", processed_query)
    if "error" in analysis_response:
        return jsonify(analysis_response), 500
    
    final_result = {
        "research": research_response,
        "analysis": analysis_response
    }
    return jsonify(final_result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)