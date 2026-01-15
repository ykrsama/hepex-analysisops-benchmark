#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import subprocess
import sys
import uuid
import time

try:
    from a2a.client import A2ACardResolver, A2AClient
    from a2a.types import MessageSendParams, SendMessageRequest
    import httpx
except ImportError:
    print("Error: 'a2a-sdk' and 'httpx' are required.")
    print("Please run this script using uv: uv run scripts/reproduce_locally.py ...")
    sys.exit(1)

# Note: EvalRequest is just a dict with {participants, config} - no import needed

# Template for docker-compose
# Note: Double braces {{ }} are used to escape them in Python's .format()
# Port mapping:
#   Both agents use internal port 9009 (AgentBeats standard)
#   Green Agent: mapped to host port 9000 (to avoid conflict)
#   Purple Agent: mapped to host port 9009
#   Inter-container communication uses container names (e.g., purple-agent:9009)
TEMPLATE = """
services:
  green-agent:
    container_name: green-agent
    image: {green_image}
    command: ["--host", "0.0.0.0", "--card-url", "http://localhost:9000/"]
    ports:
      - "9000:9009"
    environment:
      - HEPEX_DATA_DIR=/home/agent/output
    volumes:
      - ./output:/home/agent/output
    env_file:
      - .env
    depends_on:
      - purple-agent

  purple-agent:
    container_name: purple-agent
    image: {purple_image}
    command: ["--host", "0.0.0.0", "--card-url", "http://purple-agent:9009/"]
    environment:
      - HEPEX_DATA_DIR=/home/agent/output
    volumes:
      - ./output:/home/agent/output
    ports:
      - "9009:9009"
    env_file:
      - .env
"""

def generate_compose(green_image, purple_image, output_file="docker-compose.yml"):
    # We only format the image names. Env vars are handled by docker compose reading .env
    content = TEMPLATE.format(
        green_image=green_image, 
        purple_image=purple_image
    )
    with open(output_file, "w") as f:
        f.write(content)
    print(f"Generated {output_file}")

async def trigger_evaluation(green_url, purple_internal_url):
    print(f"Connecting to Green Agent at {green_url}...")
    
    # Construct the EvalRequest payload for the green agent
    eval_request = {
        "participants": {
            "white_agent": purple_internal_url
        },
        "config": {
            "task_dirs": ["specs/zpeak_fit"],
            "data_dir": "/home/agent/output"  # Use mounted volume for persistent output
        }
    }

    # Wrap in A2A message structure
    send_message_payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": json.dumps(eval_request)}],
            "messageId": uuid.uuid4().hex,
        }
    }

    # 10 min timeout to allow for data download + LLM calls
    async with httpx.AsyncClient(timeout=600.0) as httpx_client:
        # 1. Resolve agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=green_url)
        try:
            agent_card = await resolver.get_agent_card()
            print(f"Resolved Agent: {agent_card.name} ({agent_card.version})")
        except Exception as e:
            # print(f"Failed to resolve agent card at {green_url}: {e}")
            raise e

        # 2. Send the message
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            params=MessageSendParams(**send_message_payload),
        )
        
        print("Sending EvalRequest...")
        try:
            response = await client.send_message(request)
            print("Request sent successfully!")
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Reproduce the benchmark locally using Docker Compose.")
    parser.add_argument("--green-image", default="ghcr.io/ranriver/hepex-analysisops-benchmark:latest", help="Green agent image")
    parser.add_argument("--purple-image", default="ghcr.io/ranriver/hepex-analysisops-agents:latest", help="Purple agent image")
    parser.add_argument("--local", action="store_true", help="Use local images (hepex-green-agent:local / hepex-purple-agent:local)")
    parser.add_argument("--detach", "-d", action="store_true", help="Run in detached mode (don't stream logs)")
    
    args = parser.parse_args()

    # Ensure .env exists
    if not os.path.exists(".env"):
        print("Error: .env file not found. Please create one with your API keys.")
        print("Example .env content:")
        print("GOOGLE_API_KEY=AIza...")
        sys.exit(1)

    green_img = args.green_image
    purple_img = args.purple_image

    if args.local:
        green_img = "hepex-green-agent:local"
        purple_img = "hepex-purple-agent:local"

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # 1. Generate docker-compose
    generate_compose(green_img, purple_img)

    # 2. Start containers
    print("Starting containers...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True)

    try:
        # 3. Wait/Trigger loop
        print("Waiting for agents to boot...")
        
        success = False
        for i in range(15):
            print(f"Attempt {i+1}/15 to contact Green Agent...")
            try:
                success = asyncio.run(trigger_evaluation("http://localhost:9000", "http://purple-agent:9009"))
                if success:
                    break
            except Exception as e:
                # unexpected setup errors
                pass 
            
            time.sleep(5)
        
        if not success:
            print("Failed to trigger evaluation after retries.")
            sys.exit(1)

        # 4. Tail logs unless detached
        if not args.detach:
            print("\n" + "="*50)
            print("Streaming logs from containers...")
            print("NOTE: If this is the first run, the Green Agent might download ROOT files.")
            print("      Check ./output/ on your host machine to confirm.")
            print("="*50 + "\n")
            subprocess.run(["docker", "compose", "logs", "-f"])

    except KeyboardInterrupt:
        print("\nStopping...")
        
    finally:
        if not args.detach:
            print("Shutting down containers...")
            subprocess.run(["docker", "compose", "down"])

if __name__ == "__main__":
    main()
