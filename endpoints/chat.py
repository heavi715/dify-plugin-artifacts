from collections.abc import Mapping
import json
from typing import Optional
import os
import logging

from werkzeug import Request, Response
import requests

from dify_plugin import Endpoint



class Chat(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """

        app: Optional[dict] = settings.get("app")
        if not app:
            return Response("App is required", status=400)

        data = r.get_json()
        query = data.get("query")
        conversation_id = data.get("conversation_id")
        api_key = settings.get("api-key")

        if not query:
            return Response("Query is required", status=400)

        def generator():
            dify_url = os.getenv(
                "DIFY_INNER_API_URL", "https://api.dify.ai")
            url = f"{dify_url}/v1/chat-messages"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": {},
                "query": query,
                "response_mode": "streaming",
                "conversation_id": conversation_id,
                "user": "abc-123",  # 这里可以根据实际情况传递
            }
            print(url)
            print(headers)
            print(payload)
            with requests.post(url, headers=headers, json=payload, stream=True) as resp:
                for line in resp.iter_lines():
                    if line:
                        line_str = line.decode()
                        print(line_str)
                        if line_str.startswith("data:"):
                            try:
                                data_json = json.loads(line_str[5:].strip())
                                print(data_json)
                                if data_json["event"] != "message":
                                    continue
                                if data_json is not None:
                                    yield json.dumps(data_json) + "\n\n"
                            except Exception:
                                continue

        return Response(generator(), status=200, content_type="text/event-stream")
