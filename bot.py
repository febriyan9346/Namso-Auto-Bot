import requests
import json
import time
import sys
from datetime import datetime

# --- WARNA TEXT ---
class Col:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# --- KONFIGURASI ---
FARM_INTERVAL = 60       # 60 Detik
CHECKIN_INTERVAL = 86400  

active_users = []

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
    if not proxy: return "Direct"
    try:
        if "@" in proxy:
            return proxy.split("@")[1] 
        return proxy
    except:
        return "Proxy"

def get_time():
    return datetime.now().strftime('%H:%M:%S')

# --- 1. LOGIN DASHBOARD ---
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
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
            return session
        else:
            print(f"    {Col.RED}Dashboard Gagal: {data}{Col.RESET}")
            return None
    except Exception as e:
        print(f"    {Col.RED}Error Dashboard: {e}{Col.RESET}")
        return None

# --- 2. LOGIN EXTENSION (AUTO) ---
def perform_extension_auth(email, password, proxy):
    url = "https://sentry-api.namso.network/devv/api/connectAuth"
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "chrome-extension://ccdooaopgkfbikbdiekinfheklhbemcd",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
    
    proxies_dict = {'http': proxy, 'https': proxy} if proxy else None

    try:
        res = requests.post(url, json={"email": email, "password": password}, headers=headers, proxies=proxies_dict)
        if res.status_code == 200:
            data = res.json()
            token = data.get("token") or data.get("access_token")
            if token:
                return token
    except Exception as e:
        pass
    return None

# --- 3. SESSION UTILS ---
def create_farming_session(token, proxy):
    session = requests.Session()
    if proxy:
        session.proxies.update({'http': proxy, 'https': proxy})

    headers = {
        "authority": "sentry-api.namso.network",
        "accept": "*/*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "chrome-extension://ccdooaopgkfbikbdiekinfheklhbemcd",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "connection": "keep-alive"
    }
    session.headers.update(headers)
    return session

# --- 4. DATA STREAM ---
def get_dashboard_stats(session):
    ts = int(time.time() * 1000)
    url = f"https://app.namso.network/dashboard/api.php/data-stream?page=dashboard&p=1&_t={ts}"
    
    try:
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            if data.get("success") is True:
                user_data = data.get("data", {})
                
                raw_share = user_data.get("contribution", "0")
                clean_share = raw_share.replace(",", "").replace(" SHARE", "")
                
                daily_obj = user_data.get("daily_points", {})
                val_points = daily_obj.get("validator_points", [])
                
                points_today = 0
                if val_points:
                    points_today = val_points[-1]
                
                status = user_data.get("validator_status", "Unknown")
                
                return clean_share, points_today, status
    except:
        pass
    return None, None, None

# --- TASKS ---

def task_checkin(user_data):
    session = user_data['session']
    masked = mask_email(user_data['email'])
    if not session: return 

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
    dash_session = user_data['session']
    masked = mask_email(user_data['email'])
    email = user_data['email']
    password = user_data['password']
    proxy = user_data['proxy']
    
    # Init session jika kosong
    if not farm_session:
        new_token = perform_extension_auth(email, password, proxy)
        if new_token:
             user_data['farm_session'] = create_farming_session(new_token, proxy)
             farm_session = user_data['farm_session']
             print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[SYSTEM]{Col.RESET}   {masked} | {Col.YELLOW}Initial Extension Login OK{Col.RESET}")
        else:
             print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.YELLOW}[FARMING]{Col.RESET}  {masked} | {Col.YELLOW}SKIP (Gagal Auth){Col.RESET}")
             return

    url_health = "https://sentry-api.namso.network/devv/api/healthCheck"
    url_task = "https://sentry-api.namso.network/devv/api/taskSubmit"
    
    need_relogin = False
    mining_status_code = 0

    try:
        # PING & SUBMIT
        farm_session.post(url_health)
        res_submit = farm_session.post(url_task, json={})
        mining_status_code = res_submit.status_code
        
        # JIKA 401 (TOKEN EXPIRED) -> TRIGGER RE-LOGIN
        if res_submit.status_code == 401:
            need_relogin = True
            
    except Exception:
        mining_status_code = 999 # Connection Error

    # AMBIL STATUS DASHBOARD
    shares, daily, val_status = get_dashboard_stats(dash_session)
    
    # PROSES RE-LOGIN JIKA TOKEN MATI
    if need_relogin:
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.RED}[SYSTEM]{Col.RESET}   {masked} | {Col.RED}Token Expired (401). Refreshing...{Col.RESET}")
        new_token = perform_extension_auth(email, password, proxy)
        if new_token:
            user_data['farm_session'] = create_farming_session(new_token, proxy)
            print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.GREEN}[SYSTEM]{Col.RESET}   {masked} | {Col.GREEN}Token Refreshed!{Col.RESET}")
            # Coba mining ulang sekali lagi biar valid
            try:
                user_data['farm_session'].post(url_health)
                res_retry = user_data['farm_session'].post(url_task, json={})
                mining_status_code = res_retry.status_code
            except: pass
            
    # --- LOGIKA TAMPILAN STATUS ---
    if shares is not None:
        status_text = val_status
        status_color = Col.GREEN
        
        if mining_status_code == 200:
            status_text = "Online"
            status_color = Col.GREEN
        elif mining_status_code == 429:
            status_text = "Rate Limit (429)"
            status_color = Col.YELLOW
        elif mining_status_code == 500 or mining_status_code == 502:
            status_text = "Server Error (5xx)"
            status_color = Col.RED
        elif mining_status_code == 999:
            status_text = "CONNECTION ERROR"
            status_color = Col.RED
        else:
            status_text = f"MINING STOPPED ({mining_status_code})"
            status_color = Col.RED

        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.GREEN}[FARMING]{Col.RESET}  {Col.WHITE}{masked}{Col.RESET} | {status_color}Status: {status_text}{Col.RESET} | SHARES: {shares} | Daily: {daily}")
    else:
        # Fallback jika Dashboard Gagal Dibaca
        mining_msg = "Mining OK" if mining_status_code == 200 else f"Err {mining_status_code}"
        print(f"{Col.CYAN}[{get_time()}]{Col.RESET} {Col.GREEN}[FARMING]{Col.RESET}  {Col.WHITE}{masked}{Col.RESET} | {Col.YELLOW}{mining_msg} (Gagal baca Dashboard){Col.RESET}")

# --- MAIN ---

if __name__ == "__main__":
    print("\n")
    print(f"{Col.CYAN}=== NAMSO BOT: AUTO AUTH, REFRESH & MONITOR ==={Col.RESET}\n")
    
    print(f"1. Run With Proxy")
    print(f"2. Run Without Proxy")
    choice = input("Choose [1/2] -> ")
    
    use_proxy = False
    if choice == '1':
        use_proxy = True
    
    print("\n")
    
    raw_accs = read_file_lines("accounts.txt")
    if not raw_accs:
        print(f"{Col.RED}File accounts.txt kosong!{Col.RESET}")
        sys.exit()

    raw_proxies = []
    if use_proxy:
        raw_proxies = read_file_lines("proxy.txt")
        if not raw_proxies:
            print(f"{Col.YELLOW}Warning: File proxy.txt kosong. Menjalankan Tanpa Proxy...{Col.RESET}\n")
            use_proxy = False

    for i, line in enumerate(raw_accs):
        parts = line.split(':')
        if len(parts) >= 2:
            email = parts[0]
            password = parts[1]
            
            current_proxy = None
            if use_proxy and i < len(raw_proxies):
                current_proxy = raw_proxies[i]
            
            # Login Dashboard
            session_dash = perform_dashboard_login(email, password, current_proxy)
            
            # Login Extension
            print(f"{Col.CYAN}--- [2] Login Extension (Auto) ---{Col.RESET}")
            token_ext = perform_extension_auth(email, password, current_proxy)
            
            session_farm = None
            if token_ext:
                print(f"    {Col.GREEN}Extension Login Sukses!{Col.RESET}\n")
                session_farm = create_farming_session(token_ext, current_proxy)
            else:
                print(f"    {Col.RED}Gagal Extension. Akan dicoba lagi saat looping.{Col.RESET}\n")

            user_data = {
                "email": email,
                "password": password, 
                "proxy": current_proxy,
                "session": session_dash,
                "farm_session": session_farm,
                "next_checkin": time.time(), 
                "next_farm": time.time()
            }
            active_users.append(user_data)
        else:
            print(f"{Col.RED}Format salah di accounts.txt{Col.RESET}")
    
    if not active_users: sys.exit()

    print(f"{Col.CYAN}=== Memulai Loop Otomatis ({len(active_users)} Akun) ==={Col.RESET}")
    print(f"{Col.YELLOW}Interval Farming : {FARM_INTERVAL} detik{Col.RESET}\n")
    
    try:
        while True:
            current_time = time.time()
            for user in active_users:
                if current_time >= user['next_farm']:
                    task_farming_and_monitor(user)
                    user['next_farm'] = current_time + FARM_INTERVAL
                
                if user['session'] and current_time >= user['next_checkin']:
                    task_checkin(user)
                    user['next_checkin'] = current_time + CHECKIN_INTERVAL
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Col.RED}Bot dihentikan.{Col.RESET}")
