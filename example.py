import os
from dotenv import load_dotenv

load_dotenv()

from orquesta_sdk import OrquestaClient, OrquestaClientOptions

api_key = os.getenv("ORQUESTA_API_KEY")
options = OrquestaClientOptions(api_key=api_key, ttl=3600, environment="production")

client = OrquestaClient(options)

from orquesta_sdk.endpoints import OrquestaEndpointRequest

prompt = "Hoe kan ik het best een rapport voor de klant opstellen?"

request = OrquestaEndpointRequest(
    key="slack-app",
    context={},
    variables={"prompt":prompt}
)

endpoint_ref = client.endpoints.query(request)

print(endpoint_ref.content)
