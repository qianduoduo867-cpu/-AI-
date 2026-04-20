import os
import json

class AICommandHandler:
    def __init__(self, api_key=None, model="gpt-4"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.system_prompt = """You are a DevOps AI assistant. Convert user requests to Linux/Shell commands.
Return ONLY a JSON object with the command to execute.
Allowed commands: apt, yum, docker, systemctl, git, curl, wget, mkdir, chmod, chown, 
nano, vim, cat, grep, ps, top, df, free, ls, cd, pwd, echo, tar, zip, unzip, pip, npm, 
node, python, source, export, echo, kill, pgrep

Examples:
User: "install nginx"
Response: {"command": "sudo apt-get install -y nginx"}

User: "check disk usage"
Response: {"command": "df -h"}

User: "restart docker"
Response: {"command": "sudo systemctl restart docker"}

User: "install openclaw"
Response: {"command": "curl -sL https://get.openclaw.com | bash"}

Respond with only JSON, no explanation."""

    def process(self, user_message):
        if not self.api_key:
            return {"error": "No API key configured"}

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                max_tokens=200
            )
            
            result = response.choices[0].message.content
            command = json.loads(result.strip())
            return command
            
        except ImportError:
            return {"error": "openai package not installed", "command": "pip install openai"}
        except Exception as e:
            return {"error": str(e), "command": ""}

if __name__ == "__main__":
    handler = AICommandHandler()
    
    test_requests = [
        "install nginx",
        "check memory usage",
        "show running processes"
    ]
    
    for req in test_requests:
        result = handler.process(req)
        print(f"User: {req}")
        print(f"Command: {result.get('command')}")
        print()