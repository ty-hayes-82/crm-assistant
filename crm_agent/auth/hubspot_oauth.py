import http.server
import socketserver
import urllib.parse
import requests
import json

# TODO: Replace with your HubSpot App's credentials
CLIENT_ID = "20057893"
CLIENT_SECRET = "bf48526d-57e8-4af3-b6a9-a2fdffae77d2"
# This must match one of the redirect URLs in your app's configuration
REDIRECT_URI = "http://localhost:3000/oauth-callback"

TOKEN_FILE = "hubspot_tokens.json"

class HubSpotOAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/oauth-callback"):
            query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if 'code' in query_components:
                auth_code = query_components["code"][0]
                print(f"Received authorization code: {auth_code}")
                
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Authorization code received. Check your console. You can close this window.")
                
                self.exchange_code_for_token(auth_code)
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Error: Authorization code not found in callback.")
        else:
            super().do_GET()

    def exchange_code_for_token(self, auth_code):
        token_url = "https://api.hubapi.com/oauth/v1/token"
        payload = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': auth_code
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        
        print("Exchanging authorization code for tokens...")
        response = requests.post(token_url, data=payload, headers=headers)
        
        if response.status_code == 200:
            tokens = response.json()
            print("Successfully received tokens.")
            with open(TOKEN_FILE, 'w') as f:
                json.dump(tokens, f, indent=4)
            print(f"Tokens saved to {TOKEN_FILE}")
            
            # You can now use tokens['access_token']
            
            # For this server to stop after getting the token, we would need to signal the server to shut down.
            # For simplicity, this server will keep running. You can manually stop it (Ctrl+C).
            
        else:
            print(f"Error getting tokens: {response.status_code} - {response.text}")

def run_oauth_server():
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("Please update CLIENT_ID and CLIENT_SECRET in the script.")
        return

    PORT = 3000
    with socketserver.TCPServer(("", PORT), HubSpotOAuthHandler) as httpd:
        print(f"Serving at port {PORT}")
        print(f"1. Go to your HubSpot app installation URL.")
        print(f"2. Authorize the app.")
        print(f"3. You will be redirected to {REDIRECT_URI}")
        print(f"4. The server will capture the auth code and get the tokens.")
        httpd.serve_forever()

if __name__ == "__main__":
    run_oauth_server()
