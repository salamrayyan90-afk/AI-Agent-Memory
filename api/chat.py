import json
import os
from http.server import BaseHTTPRequestHandler
from groq import Groq

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        user_message = data.get('message', '')

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        try:
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": user_message}]
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {str(e)}"

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'reply': reply}).encode('utf-8'))