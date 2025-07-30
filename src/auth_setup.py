import os

from composio import Composio
from composio.types import auth_scheme
from dotenv import load_dotenv

load_dotenv()

# Replace these with your actual values
github_auth_config_id = os.getenv("GITHUB_AUTH_CONFIG_ID")
user_id = os.getenv("USER_ID")

composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))

print(github_auth_config_id)
print(user_id)


def authenticate_toolkit(user_id: str, auth_config_id: str):
    connection_request = composio.connected_accounts.initiate(
        user_id=user_id,
        auth_config_id=auth_config_id,
    )

    print(f"Visit this URL to authenticate GitHub: {connection_request.redirect_url}")

    # This will wait for the auth flow to be completed
    connection_request.wait_for_connection(timeout=15)
    return connection_request.id


connection_id = authenticate_toolkit(user_id, github_auth_config_id)

# You can also verify the connection status using:
connected_account = composio.connected_accounts.get(connection_id)
print(f"Connected account: {connected_account}")
