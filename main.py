import requests
import random
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from retry import retry
from tqdm import tqdm  


logging.basicConfig(level=logging.INFO)



def fetch_and_save_proxies(api_url, file_path):
    try:
        res = requests.get(api_url)
        res.raise_for_status()  
        
        formatted = [{"protocol": i.split("://")[0].upper(), "ip": i.split("://")[1].split(":")[0], "port": i.split("://")[1].split(":")[1]} for i in res.text.split("\n") if i]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=4)
        logging.info("Proxies data saved to data.json")
    except requests.RequestException as e:
        logging.error(f"Error fetching proxies: {e}")



def load_proxies(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            proxies = json.load(f)
        return proxies
    except FileNotFoundError:
        logging.error("data.json not found. Run fetch_and_save_proxies() first.")
        return []



def save_good_proxies(proxies, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(proxies, f, indent=4)
    logging.info("Good proxies saved to good_proxies.json")



@retry(exceptions=requests.RequestException, tries=1, delay=0.5, backoff=1)
def make_request_with_proxy(url, proxy):
    proxy_url = f"{proxy['protocol'].lower()}://{proxy['ip']}:{proxy['port']}"
    response = requests.get(url, proxies={proxy['protocol'].lower(): proxy_url}, timeout=10)
    response.raise_for_status()  
    
    return proxy



api_url = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text"


file_path = "data.json"


good_proxies_file_path = "good_proxies.json"


url_to_fetch = "https://httpbin.org/ip"



fetch_and_save_proxies(api_url, file_path)



proxies = load_proxies(file_path)



if proxies:
    
    
    def process_proxy(proxy):
     
        try:
            return make_request_with_proxy(url_to_fetch, proxy)
        except requests.RequestException as e:
            logging.error(f"Error occurred with proxy {proxy['ip']}: {e}")
            return None

    
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        
        
        results = list(tqdm(executor.map(process_proxy, proxies), total=len(proxies), desc="Checking Proxies"))

    
    
    good_proxies = [proxy for proxy in results if proxy]

    if good_proxies:
        
        
        save_good_proxies(good_proxies, good_proxies_file_path)
    else:
        logging.error("No good proxies found.")
else:
    logging.error("No proxies available. Check data.json or fetch proxies using fetch_and_save_proxies().")
