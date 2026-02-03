import requests
import time

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server
    for i in range(30):
        try:
            resp = requests.get(base_url + "/")
            if resp.status_code == 200:
                print("Server is up!")
                break
        except:
            time.sleep(2)
    else:
        print("Server failed to start.")
        return

    # Create dummy file
    with open("test.txt", "w") as f:
        f.write("The secret code is ALPHA-BETA-GAMMA. The projected revenue for Q4 is $5M.")
        
    # Upload
    print("Uploading file...")
    with open("test.txt", "rb") as f:
        files = {'file': f}
        resp = requests.post(f"{base_url}/upload", files=files)
        print("Upload response:", resp.json())

    # Chat
    print("Asking question...")
    query = {"query": "What is the projected revenue for Q4?"}
    resp = requests.post(f"{base_url}/chat", json=query)
    print("Chat response:", resp.json())
    
    query2 = {"query": "What is the secret code?"}
    resp2 = requests.post(f"{base_url}/chat", json=query2)
    print("Chat response 2:", resp2.json())

if __name__ == "__main__":
    test_api()
