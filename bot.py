import requests
import json
import time
import sys
import uuid
from datetime import datetime

class Col:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

FARM_INTERVAL = 60
CHECKIN_INTERVAL = 86400
active_users = []
MIN_SYNC_INTERVAL = 300  # 5 menit minimum antara sync

def read_file_lines(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def mask_email(email):
    if "@" in email:
        parts = email.split("@")
        user = parts[0]
        domain = parts[1]
        if len(user) > 3:
            return f"{user[:3]}***@{domain}"
        return f"{user[:1]}***@{domain}"
    return email

def mask_proxy(proxy):
    if not proxy:
        return "Direct"
    try:
        if "@" in proxy:
            return proxy.split("@")[1]
        return proxy
    except:
        return "Proxy"

def get_time():
    return datetime.now().strftime('%H:%M:%S')

def perform_dashboard_login(email, password, proxy):
    session = requests.Session()
    if proxy:
        session.proxies.update({'http': proxy, 'https': proxy})
    
    headers = {
        "authority": "app.namso.network",
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://app.namso.network",
        "referer": "https://app.namso.network/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    session.headers.update(headers)
    url_login = "https://app.namso.network/login.php"
    
    masked_email = mask_email(email)
    masked_proxy = mask_proxy(proxy)
    print(f"{Col.CYAN}--- [1] Login Dashboard: {masked_email} | IP: {masked_proxy} ---{Col.RESET}")
    
    try:
        session.post(url_login, json={"email": email, "password": password, "action": "validate_credentials"})
        session.post(url_login, json={"email": email, "action": "send_otp"})
        print(f"    {Col.YELLOW}OTP Dikirim ke email.{Col.RESET}")
        
        otp_code = input(f"    {Col.YELLOW}Masukkan OTP untuk {masked_email}: {Col.RESET}")
        
        res3 = session.post(url_login, json={"email": email, "password": password, "otp": otp_code, "action": "login"})
        data = res3.json()
        
        if data.get("success") is True or data.get("status") == "success":
            print(f"    {Col.GREEN}Dashboard Login Sukses!{Col.RESET}")
            dashboard_token = data.get('token') or data.get('access_token')
            return session, dashboard_token
        else:
            print(f"    {Col.RED}Dashboard Gagal: {data}{Col.RESET}")
            return None, None
    except Exception as e:
        print(f"    {Col.RED}Error Dashboard: {e}{Col.RESET}")
        return None, None

def perform_extension_auth(email, password, proxy):
    url = "https://sentry-api.namso.network/devv/api/connectAuth"
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "chrome-extension://ccdooaopgkfbikbdiekinfheklhbemcd",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    proxies_dict = {'http': proxy, 'https': proxy} if proxy else None
    
    try:
        res = requests.post(url, json={"email": email, "password": password}, headers=headers, proxies=proxies_dict, timeout=15)
        if res.status_code == 200:
            data = res.json()
            token = data.get("token") or data.get("access_token")
            if token:
                return token
    except Exception as e:
        pass
    return None

def create_farming_session(token, proxy):
    session = requests.Session()
    if proxy:
        session.proxies.update({'http': proxy, 'https': proxy})
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {token}",
        "cache-control": "no-cache",
        "connection": "keep-alive",
        "content-type": "application/json",
        "host": "sentry-api.namso.network",
        "origin": "chrome-extension://ccdooaopgkfbikbdiekinfheklhbemcd",
        "pragma": "no-cache",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "none",
        "sec-fetch-storage-access": "active",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    session.headers.update(headers)
    return session

def setup_validator_node(session):
    base_info = {
        "device_id": str(uuid.uuid4()),
        "version": "1.0.1",
        "uptime": 0
    }
    
    ip_address = None
    
    try:
        temp_session = requests.Session()
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        if hasattr(session, 'proxies') and session.proxies:
            r = session.get("https://api.ipify.org?format=json", headers=headers, timeout=10)
        else:
            r = temp_session.get("https://api.ipify.org?format=json", headers=headers, timeout=10)
        
        if r.status_code == 200:
            ip_address = r.json().get('ip')
            print(f"    {Col.GREEN}[Validator] IP: {ip_address}{Col.RESET}")
    except Exception as e:
        print(f"    {Col.RED}[Validator] Error get IP: {e}{Col.RESET}")
    
    if not ip_address:
        try:
            if hasattr(session, 'proxies') and session.proxies:
                r = session.get("https://ipinfo.io/json", headers=headers, timeout=10)
            else:
                r = requests.get("https://ipinfo.io/json", headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                ip_address = data.get('ip')
                print(f"    {Col.GREEN}[Validator] IP from ipinfo: {ip_address}{Col.RESET}")
        except:
            pass
    
    if not ip_address:
        print(f"    {Col.RED}[Validator] CRITICAL: No IP detected!{Col.RESET}")
        base_info.update({"ip": "0.0.0.0", "city": "Unknown", "country": "XX"})
        return base_info
    
    try:
        if hasattr(session, 'proxies') and session.proxies:
            r = session.get(f"https://ipinfo.io/{ip_address}/json", headers=headers, timeout=10)
        else:
            r = requests.get(f"https://ipinfo.io/{ip_address}/json", headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            base_info.update({
                "ip": data.get('ip', ip_address),
                "city": data.get('city', 'Unknown'),
                "region": data.get('region', 'Unknown'),
                "country": data.get('country', 'XX'),
                "loc": data.get('loc', '0,0'),
                "org": data.get('org', 'Unknown'),
                "postal": data.get('postal', ''),
                "timezone": data.get('timezone', 'UTC')
            })
            print(f"    {Col.GREEN}[Validator] Location: {data.get('city')}, {data.get('country')}{Col.RESET}")
            return base_info
    except Exception as e:
        print(f"    {Col.RED}[Validator] Error geolocation: {e}{Col.RESET}")
    
    base_info.update({
        "ip": ip_address,
        "city": "Unknown",
        "country": "XX",
        "loc": "0,0",
        "org": "Unknown",
        "timezone": "UTC"
    })
    return base_info

def task_checkin(user_data):
    session = user_data['session']
    masked = mask_email(user_data['email'])
    if not session:
        return
    
    url_checkin = "https://app.namso.network/dashboard/api.php/checkin"
    try:
        res = session.post(url_checkin)
        msg = res.json().get("message", res.text[:50])
        color = Col.GREEN if "Success" in str(msg) or "already" in str(msg) else Col.RED
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {color}[CHECK-IN]{Col.RESET} {Col.WHITE}{masked}{Col.RESET} | {color}{msg}{Col.RESET}")
    except:
        pass

def task_farming_and_monitor(user_data):
    farm_session = user_data['farm_session']
    masked = mask_email(user_data['email'])
    email = user_data['email']
    password = user_data['password']
    proxy = user_data['proxy']
    
    if not farm_session:
        new_token = perform_extension_auth(email, password, proxy)
        if new_token:
            user_data['farm_session'] = create_farming_session(new_token, proxy)
            farm_session = user_data['farm_session']
            print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[SYSTEM]{Col.RESET} {masked} | Ext Login OK")
            user_data['geo_info'] = setup_validator_node(farm_session)
            user_data['start_time'] = time.time()
        else:
            print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[FARMING]{Col.RESET} {masked} | SKIP")
            return
    
    url_health = "https://sentry-api.namso.network/devv/api/healthCheck"
    url_task = "https://sentry-api.namso.network/devv/api/taskSubmit"
    
    need_relogin = False
    farming_success = False
    rate_limited = False
    shares = "N/A"
    points_today = "N/A"
    
    try:
        elapsed_seconds = int(time.time() - user_data.get('start_time', time.time()))
        
        # HEALTH CHECK
        health_res = farm_session.post(url_health, timeout=15)
        
        if health_res.status_code == 401:
            need_relogin = True
            raise Exception("Token expired")
        
        # TASK SUBMIT - Dengan email di body!
        payload = {"email": email}
        
        res_submit = farm_session.post(url_task, json=payload, timeout=15)
        
        if res_submit.status_code == 401:
            need_relogin = True
            raise Exception("Token expired")
        
        if res_submit.status_code == 200:
            data = res_submit.json()
            if data.get('success'):
                farming_success = True
                shares = data.get('shares', 'N/A')
                points_today = data.get('points_today', 'N/A')
                
                # Simpan next_sync untuk scheduling optimal
                next_sync = data.get('next_sync')
                if next_sync:
                    # Convert timestamp to interval
                    next_sync_time = next_sync - int(time.time())
                    if next_sync_time > 0:
                        user_data['optimal_interval'] = next_sync_time
                        print(f"    {Col.GREEN}[Info] Next sync in {next_sync_time}s{Col.RESET}")
            else:
                error_msg = data.get('error', 'Unknown')
                if 'too frequent' in error_msg.lower() or 'sync' in error_msg.lower():
                    # Server bilang terlalu cepat, tunggu lebih lama
                    rate_limited = True
                    user_data['optimal_interval'] = MIN_SYNC_INTERVAL
                    print(f"    {Col.YELLOW}[Warning] {error_msg} - Next sync in {MIN_SYNC_INTERVAL}s{Col.RESET}")
                elif 'invalid session' in error_msg.lower() or 'session' in error_msg.lower():
                    # Session invalid, perlu re-login
                    need_relogin = True
                    print(f"    {Col.RED}[Error] {error_msg} - Re-authenticating...{Col.RESET}")
                else:
                    print(f"    {Col.RED}[Error] {error_msg}{Col.RESET}")
        else:
            print(f"    {Col.RED}[Error] Status {res_submit.status_code}{Col.RESET}")
    
    except Exception as e:
        error_msg = str(e)
        if "401" not in error_msg and "Token" not in error_msg:
            print(f"    {Col.RED}[Error] {error_msg[:100]}{Col.RESET}")
    
    if need_relogin:
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.RED}[SYSTEM]{Col.RESET} {masked} | Session Invalid - Re-authenticating...")
        new_token = perform_extension_auth(email, password, proxy)
        if new_token:
            user_data['farm_session'] = create_farming_session(new_token, proxy)
            user_data['geo_info'] = setup_validator_node(user_data['farm_session'])
            user_data['start_time'] = time.time()
            print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.GREEN}[SYSTEM]{Col.RESET} {masked} | Token Refreshed - Retrying...")
            
            # Retry farming immediately after refresh
            try:
                farm_session = user_data['farm_session']
                health_res = farm_session.post(url_health, timeout=15)
                payload = {"email": email}
                res_submit = farm_session.post(url_task, json=payload, timeout=15)
                
                if res_submit.status_code == 200:
                    data = res_submit.json()
                    if data.get('success'):
                        farming_success = True
                        shares = data.get('shares', 'N/A')
                        points_today = data.get('points_today', 'N/A')
                        
                        next_sync = data.get('next_sync')
                        if next_sync:
                            next_sync_time = next_sync - int(time.time())
                            if next_sync_time > 0:
                                user_data['optimal_interval'] = next_sync_time
                        
                        print(f"    {Col.GREEN}[Success] Retry succeeded after token refresh{Col.RESET}")
            except Exception as retry_err:
                print(f"    {Col.RED}[Error] Retry failed: {str(retry_err)[:50]}{Col.RESET}")
    
    elapsed = int(time.time() - user_data.get('start_time', time.time()))
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    uptime_str = f"{hours}h {minutes}m"
    
    if farming_success:
        if isinstance(shares, (int, float)):
            shares_str = f"{shares:,.4f}"
        else:
            shares_str = str(shares)
        
        if isinstance(points_today, (int, float)):
            points_str = f"{points_today:.2f}"
        else:
            points_str = str(points_today)
        
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.GREEN}[FARMING]{Col.RESET} {Col.WHITE}{masked}{Col.RESET} | {Col.GREEN}✓ Online{Col.RESET} | SHARES: {shares_str} | Today: {points_str} | Uptime: {uptime_str}")
    elif rate_limited:
        next_interval = user_data.get('optimal_interval', MIN_SYNC_INTERVAL)
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[FARMING]{Col.RESET} {Col.WHITE}{masked}{Col.RESET} | {Col.YELLOW}⏳ Rate Limited{Col.RESET} | Next sync in {next_interval}s | Uptime: {uptime_str}")
    else:
        status_text = "Token Expired" if need_relogin else "✗ Failed"
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[FARMING]{Col.RESET} {Col.WHITE}{masked}{Col.RESET} | {Col.RED}{status_text}{Col.RESET} | Uptime: {uptime_str}")

if __name__ == "__main__":
    print(f"\n{Col.CYAN}=== NAMSO BOT: AUTO FARMING ==={Col.RESET}\n")
    
    print("1. Run With Proxy")
    print("2. Run Without Proxy")
    choice = input("Choose [1/2] -> ")
    
    use_proxy = (choice == '1')
    print()
    
    raw_accs = read_file_lines("accounts.txt")
    if not raw_accs:
        print(f"{Col.RED}File accounts.txt kosong!{Col.RESET}")
        sys.exit()
    
    raw_proxies = []
    if use_proxy:
        raw_proxies = read_file_lines("proxy.txt")
        if not raw_proxies:
            print(f"{Col.YELLOW}Warning: proxy.txt kosong.{Col.RESET}\n")
            use_proxy = False
    
    for i, line in enumerate(raw_accs):
        parts = line.split(':')
        if len(parts) >= 2:
            email = parts[0]
            password = parts[1]
            
            current_proxy = None
            if use_proxy and i < len(raw_proxies):
                current_proxy = raw_proxies[i]
            
            result = perform_dashboard_login(email, password, current_proxy)
            
            if result:
                session_dash, dashboard_token = result
            else:
                session_dash, dashboard_token = None, None
            
            print(f"{Col.CYAN}--- [2] Login Extension ---{Col.RESET}")
            token_ext = perform_extension_auth(email, password, current_proxy)
            
            final_token = dashboard_token if dashboard_token else token_ext
            
            session_farm = None
            geo_info = {}
            if final_token:
                print(f"    {Col.GREEN}Login Sukses!{Col.RESET}")
                session_farm = create_farming_session(final_token, current_proxy)
                print(f"    {Col.YELLOW}Setup Node...{Col.RESET}")
                geo_info = setup_validator_node(session_farm)
                print(f"    {Col.GREEN}Ready! IP: {geo_info.get('ip')}{Col.RESET}\n")
            else:
                print(f"    {Col.RED}Gagal Login.{Col.RESET}\n")
            
            user_data = {
                "email": email,
                "password": password,
                "proxy": current_proxy,
                "session": session_dash,
                "farm_session": session_farm,
                "geo_info": geo_info,
                "start_time": time.time(),
                "next_checkin": time.time(),
                "next_farm": time.time(),
                "optimal_interval": FARM_INTERVAL
            }
            active_users.append(user_data)
        else:
            print(f"{Col.RED}Format salah di accounts.txt{Col.RESET}")
    
    if not active_users:
        sys.exit()
    
    print(f"{Col.CYAN}=== Loop Otomatis ({len(active_users)} Akun) ==={Col.RESET}")
    print(f"{Col.YELLOW}Interval: {FARM_INTERVAL} detik{Col.RESET}\n")
    
    try:
        while True:
            current_time = time.time()
            for user in active_users:
                if current_time >= user['next_farm']:
                    task_farming_and_monitor(user)
                    
                    # Set next farm time berdasarkan optimal_interval
                    interval = user.get('optimal_interval', FARM_INTERVAL)
                    user['next_farm'] = current_time + interval
                
                if user['session'] and current_time >= user['next_checkin']:
                    task_checkin(user)
                    user['next_checkin'] = current_time + CHECKIN_INTERVAL
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Col.RED}Bot dihentikan.{Col.RESET}")
