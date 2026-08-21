import os
import shutil
import asyncio
import json
import base64
import requests
import time
import uuid
import random
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==========================================
# تنظیمات پایه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ مقدار BOT_TOKEN پیدا نشد!")

router = Router()

SESSION_BASE_DIR = "bot_sessions"
if os.path.exists(SESSION_BASE_DIR):
    shutil.rmtree(SESSION_BASE_DIR, ignore_errors=True)
os.makedirs(SESSION_BASE_DIR, exist_ok=True)

# ---------------- وضعیت‌ها و کیبورد ----------------
class BotStates(StatesGroup):
    waiting_for_sync_links = State()
    waiting_for_delete_links = State()
    waiting_for_discount_links = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 همگام‌سازی سبد خرید")],
        [KeyboardButton(text="🗑 پاک کردن آدرس‌ها"), KeyboardButton(text="🔎 بررسی تخفیف‌ها")]
    ],
    resize_keyboard=True
)

# ---------------- لیست پروکسی‌ها ----------------
PROXY_LIST = [
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.7.126:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.230.150:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.23.131:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.55.136:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.13.20:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.62.232:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.189.86:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.34.222:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.233.174:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.241.244:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.236.215:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.251.13:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.28.96:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.251.174:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@217.181.92.238:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.0.145:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.167.19.4:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.22.213:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.47.222:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.4.62:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.190.140:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.53.131:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.184.112:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.249.51:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.245.102:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.35.92:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.4.117:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@151.123.178.245:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.237.136:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.26.1:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.50.74:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.239.108:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.33.33:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.171.178:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.43.234:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.51.147:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.252.153:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.15.12:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.249.210:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.48.36:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.39.59:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@151.123.178.113:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.239.57:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.189.37:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.50.103:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.48.129:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.25.235:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.36.104:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.28.117:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.236.228:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.163.127:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.235.116:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.34.137:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.28.221:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.40.220:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.165.47:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.44.75:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.183.220:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.232.214:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.184.134:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.47.172:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.25.248:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.167.19.14:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@217.181.90.180:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.5.0:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.53.63:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.40.35:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.179.125:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.251.56:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.3.241:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.4.73:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.32.129:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.31.240:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.245.224:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.243.136:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@193.56.28.116:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.31.27:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.30.161:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.13.49:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.227.15:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@151.123.176.204:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.40.10:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.24.72:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.51.69:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.2.30:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.253.207:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.43.102:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.247.58:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.33.67:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@45.3.52.56:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.11.167:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.251.71:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.55.31:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.29.89:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@65.111.20.185:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.177.17:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@104.207.39.238:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.241.164:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@216.26.242.29:3129",
    "http://u9ocz1sriwce:vn4f73h2wcjl6w4@209.50.173.132:3129"
]

# ==========================================
# توابع کمکی
# ==========================================
def get_random_proxy():
    selected = random.choice(PROXY_LIST)
    return {"http": selected, "https": selected}

def fetch_data(url):
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def get_tokens_from_data(data):
    access_token, refresh_token = None, None
    try:
        for cookie in data.get('cookies', []):
            if cookie.get('name') == 'tokenMS':
                access_token = cookie.get('value')
            elif cookie.get('name') == 'refresh_token':
                refresh_token = cookie.get('value')
        if not access_token or not refresh_token:
            for origin in data.get('origins', []):
                for item in origin.get('localStorage', []):
                    if item.get('name') == 'tokenMS':
                        access_token = item.get('value')
                    elif item.get('name') == 'refresh_token':
                        refresh_token = item.get('value')
    except Exception:
        pass
    return access_token, refresh_token

def update_tokens_in_data(data, old_acc, new_acc, old_ref, new_ref):
    try:
        content = json.dumps(data, ensure_ascii=False)
        if old_acc and new_acc:
            content = content.replace(old_acc, new_acc)
        if old_ref and new_ref:
            content = content.replace(old_ref, new_ref)
        return json.loads(content)
    except Exception:
        return data

def get_user_id_from_token(token):
    # ❌ مشکل برطرف شد: cerberusId عدد نیست، فقط userId و alternativeCustomerId عددی هستند
    try:
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded_bytes)
        uid = data.get('userId') or data.get('alternativeCustomerId')
        if uid: return int(uid)
        return 0
    except Exception:
        return 0

async def extract_urls_from_message(message: Message, bot: Bot):
    if message.text:
        return re.findall(r'(https?://\S+)', message.text)
    elif message.document:
        if not message.document.file_name.lower().endswith('.txt'):
            return []
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        content = downloaded_file.read().decode('utf-8', errors='ignore')
        return re.findall(r'(https?://\S+)', content)
    return []

# ==========================================
# کلاس ارتباط با API اُکالا
# ==========================================
class OkalaAPI:
    def __init__(self):
        self.request_logs = []
        self.base_headers = {
            'accept': 'application/json, text/plain, */*',
            'source': 'okala',
            'ui-version': '2.0',
            'origin': 'https://www.okala.com',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137.0.0.0 Mobile'
        }

    def log_request(self, method, url, status_code, response_text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {method} {url}\nStatus: {status_code}\nResponse: {response_text}\n{'-'*50}\n"
        self.request_logs.append(log_entry)

    def make_request(self, method, url, access_token=None, **kwargs):
        headers = self.base_headers.copy()
        headers['X-Correlation-Id'] = str(uuid.uuid4())
        headers['X-User-Unique-Id'] = str(uuid.uuid4())
        headers['session-id'] = str(uuid.uuid4())

        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'

        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        for attempt in range(3):
            current_proxy = get_random_proxy()
            try:
                res = requests.request(method, url, headers=headers, proxies=current_proxy, timeout=45, **kwargs)
                self.log_request(method, url, res.status_code, res.text)
                if res.status_code == 200:
                    try: return 200, res.json()
                    except: return 200, {}
                elif res.status_code == 401: return 401, {}
                else: return res.status_code, res.text 
            except Exception as e:
                self.log_request(method, url, "EXCEPTION", str(e))
                time.sleep(1.5)
                continue
        return 0, "Network Error"

    def refresh_token(self, refresh_token):
        url = "https://apigateway.okala.com/api/v1/accounts/tokens"
        data = {"grant_type": "refresh_token", "client_id": "customer_client_id", "client_secret": "u_M{'57j!%LI21#", "scope": "offline_access", "refresh_token": refresh_token}
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status, response_data = self.make_request('POST', url, headers=headers, data=data)
        if status == 200 and isinstance(response_data, dict):
            return response_data.get('access_token'), response_data.get('refresh_token')
        return None, None

    # --- متدهای مربوط به آدرس ---
    def get_address(self, token, uid):
        url = 'https://apigateway.okala.com/api/voyager/CustomerAddress/CustomerAddressForReact'
        return self.make_request('GET', url, token, params={'customerId': uid})

    def get_all_addresses_paged(self, token, page_size=50):
        url = f'https://apigateway.okala.com/api/v1/accounts/userprofile/getcustomeraddresseswithpaging?pageIndex=1&pageSize={page_size}'
        return self.make_request('GET', url, token)

    def add_address(self, token, uid, addr_data):
        url = 'https://apigateway.okala.com/api/voyager/C/CustomerAccount/AddAddress/'
        
        # ❌ مشکل برطرف شد: جلوگیری از ارسال آدرس خالی (که باعث ارور سرور می‌شود)
        addr_text = addr_data.get('address')
        if not addr_text or not str(addr_text).strip():
            addr_text = "آدرس ثبت شده از نقشه"
            
        payload = {
            'id': 0, 
            'customerId': int(uid), 
            'mobilePhone': '', 
            'ShoppingSectorPartId': '0',
            'shoppingSectorId': '0', 
            'plaque': str(addr_data.get('plaque') or '0'), 
            'unit': str(addr_data.get('unit') or '1'), 
            'lat': float(addr_data.get('lat', 35.69975)),
            'lng': float(addr_data.get('lng', 51.33551)), 
            'title': None, 
            'addressTypeId': 3, 
            'oprationDuration': random.randint(10000, 20000), 
            'address': addr_text,
            'mapPlatform': 'ParsiMap'
        }
        return self.make_request('POST', url, token, json=payload)

    def delete_address(self, token, address_id):
        url = f'https://apigateway.okala.com/api/voyager/C/CustomerAccount/DeleteAddress/{address_id}/'
        return self.make_request('DELETE', url, token)

    # --- متدهای سبد خرید ---
    def get_stores(self, token, lat, lng, uid):
        url = 'https://apigateway.okala.com/api/opex/v4/stores/nearby'
        return self.make_request('GET', url, token, params={'latitude': lat, 'longitude': lng})

    def get_cart(self, token, uid, store_ids):
        url = 'https://apigateway.okala.com/api/Basket/v4/ShoppingCart/GetCustomerShoppingCartItems'
        return self.make_request('GET', url, token, params={'CustomerId': uid, 'StoreIds': store_ids, 'isFromCartPage': 'false'})

    def add_to_cart(self, token, uid, store_id, product_id):
        url = 'https://apigateway.okala.com/api/Basket/v2/ShoppingCart/AddToShoppingCart'
        payload = {'storeId': store_id, 'customerId': uid, 'productId': product_id, 'quantity': 1, 'isSupplier': False, 'replaceItemMethodCode': -1, 'sectorId': '0', 'sectorPartId': '0', 'productStoreId': '0', 'queryId': None}
        return self.make_request('POST', url, token, json=payload)

    # --- متدهای تخفیف ---
    def get_discounts(self, token, uid):
        url = f"https://apigateway.okala.com/api/discount/v1/discounts/customer/{uid}"
        return self.make_request('GET', url, token)


# ==========================================
# توابع پردازشگر (Workers)
# ==========================================

# --- 1. کپی سبد خرید ---
def worker_copy_basket(target_url, api, template_data):
    time.sleep(random.uniform(0.1, 1.0))
    data = fetch_data(target_url)
    if not data: return target_url, "error_fetch", None, ["دریافت اطلاعات اکانت از لینک ناموفق بود."]
    
    acc_token, ref_token = get_tokens_from_data(data)
    if not acc_token: return target_url, "error_token", data, ["توکن در اطلاعات اکانت یافت نشد."]

    uid = get_user_id_from_token(acc_token)
    if not uid or uid == 0: return target_url, "error_uuid", data, ["شناسه کاربری (User ID) معتبر نیست."]

    status, response_data = api.add_address(acc_token, uid, template_data['address'])
    if status == 401 and ref_token:
        new_acc, new_ref = api.refresh_token(ref_token)
        if new_acc:
            data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
            acc_token = new_acc
            status, response_data = api.add_address(acc_token, uid, template_data['address'])

    if status != 200: 
        return target_url, "error_address", data, [f"خطا در ثبت آدرس | HTTP Status: {status} | Response: {response_data}"]

    added_count = 0
    cart_errors = []
    
    for item in template_data['items']:
        for _ in range(item['quantity']):
            c_status, c_res = api.add_to_cart(acc_token, uid, template_data['store_id'], item['productId'])
            if c_status == 200: 
                added_count += 1
            else:
                cart_errors.append(f"خطا در افزودن محصول {item.get('productId')} | HTTP Status: {c_status} | Response: {c_res}")
            time.sleep(random.uniform(0.3, 0.8))

    if added_count == 0 and len(template_data['items']) > 0:
        return target_url, "error_cart", data, cart_errors

    return target_url, "success", data, cart_errors

def process_all_links(session_dir, template_url, target_urls):
    api = OkalaAPI()
    template_data_json = fetch_data(template_url)
    if not template_data_json: return None, None, "خطا: دریافت اطلاعات اکانت مرجع ناموفق بود.", None

    t_acc, t_ref = get_tokens_from_data(template_data_json)
    t_uid = get_user_id_from_token(t_acc)
    if not t_uid or t_uid == 0: return None, None, "خطا: توکن اکانت مرجع معتبر نیست.", None

    status, addr_res = api.get_address(t_acc, t_uid)
    if status == 401 and t_ref:
        t_acc, t_ref = api.refresh_token(t_ref)
        if t_acc:
            template_data_json = update_tokens_in_data(template_data_json, t_acc, t_acc, t_ref, t_ref)
            status, addr_res = api.get_address(t_acc, t_uid)

    template_addr = None
    if status == 200 and isinstance(addr_res, dict) and addr_res.get('data'):
        template_addr = addr_res['data'][0]
    else:
        lat, lng, addr_text = 35.69975, 51.33551, "آدرس استخراج شده"
        template_addr = {'lat': lat, 'lng': lng, 'address': addr_text, 'plaque': '0', 'unit': '1'}

    status, stores_res = api.get_stores(t_acc, template_addr['lat'], template_addr['lng'], t_uid)
    if status != 200 or not isinstance(stores_res, dict) or not stores_res.get('data', {}).get('stores'):
        return None, api.request_logs, f"خطا: هیچ فروشگاهی برای مختصات اکانت مرجع یافت نشد. (HTTP Status: {status})", None

    store_ids = [s['storeId'] for s in stores_res['data']['stores']]
    status, cart_res = api.get_cart(t_acc, t_uid, store_ids)
    if status != 200 or not isinstance(cart_res, dict) or not cart_res.get('data', {}).get('result'):
        return None, api.request_logs, f"خطا: امکان بازیابی سبد خرید اکانت مرجع وجود ندارد. (HTTP Status: {status})", None

    cart_data = cart_res['data']['result'][0]
    cart_items = cart_data.get('items', [])
    if not cart_items: return None, api.request_logs, "خطا: سبد خرید اکانت مرجع خالی است.", None

    template_data = {
        'address': template_addr,
        'store_id': cart_data.get('storeId'),
        'items': cart_items
    }

    stats = {"total_targets": len(target_urls), "success": 0, "error_fetch": 0, "error_address": 0, "error_cart": 0, "error_token": 0}
    all_errors = []
    
    updated_dir = os.path.join(session_dir, "Updated_Accounts")
    os.makedirs(updated_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(worker_copy_basket, url, api, template_data): url for url in target_urls}
        counter = 1
        for future in as_completed(futures):
            url = futures[future]
            try:
                _, result, updated_json, c_errs = future.result()
                if result == "success": stats["success"] += 1
                elif result == "error_fetch": stats["error_fetch"] += 1
                elif result in ["error_token", "error_uuid"]: stats["error_token"] += 1
                elif result == "error_address": stats["error_address"] += 1
                elif result == "error_cart": stats["error_cart"] += 1
                
                if c_errs:
                    all_errors.append(f"🔗 لینک اکانت:\n{url}\n" + "\n".join(c_errs) + "\n" + "-"*40)
                    
                if updated_json:
                    file_name = f"target_account_{counter}.json"
                    with open(os.path.join(updated_dir, file_name), "w", encoding="utf-8") as f:
                        json.dump(updated_json, f, ensure_ascii=False, indent=2)
                counter += 1
            except Exception as e:
                stats["error_fetch"] += 1
                all_errors.append(f"🔗 لینک اکانت:\n{url}\nخطای پردازش: {str(e)}\n" + "-"*40)

    zip_path = shutil.make_archive(os.path.join(session_dir, "Updated_Accounts_Data"), 'zip', updated_dir)
    
    error_file_path = None
    if all_errors:
        error_file_path = os.path.join(session_dir, "Server_Errors.txt")
        with open(error_file_path, "w", encoding="utf-8") as f:
            f.write("گزارش دقیق خطاهای سرور در ثبت آدرس و افزودن سبد خرید:\n============================================================\n\n")
            f.write("\n".join(all_errors))
            
    return (zip_path, template_data, stats, error_file_path), api.request_logs, None


# --- 2. پاک کردن آدرس‌ها ---
def worker_delete_addresses(target_url, api):
    time.sleep(random.uniform(0.1, 1.0))
    data = fetch_data(target_url)
    if not data: return target_url, "error_fetch", 0
    
    acc_token, ref_token = get_tokens_from_data(data)
    if not acc_token: return target_url, "error_token", 0

    total_deleted = 0
    for attempt in range(10): 
        status, addr_res = api.get_all_addresses_paged(acc_token, page_size=50)
        if status == 401 and ref_token:
            new_acc, _ = api.refresh_token(ref_token)
            if new_acc:
                acc_token = new_acc
                status, addr_res = api.get_all_addresses_paged(acc_token, page_size=50)

        if status != 200 or not isinstance(addr_res, dict):
            if attempt == 0: return target_url, "error_fetch_address", total_deleted
            else: break

        addresses = addr_res.get('data', {}).get('customerAddressResponseItems', [])
        if not addresses: break
            
        for addr in addresses:
            addr_id = addr.get('id')
            if addr_id:
                del_status, _ = api.delete_address(acc_token, addr_id)
                if del_status == 200: total_deleted += 1
                time.sleep(random.uniform(0.3, 0.8))

    return target_url, "success", total_deleted

def process_delete_all_links(session_dir, target_urls):
    api = OkalaAPI()
    stats = {"total_targets": len(target_urls), "success_accounts": 0, "total_deleted_addresses": 0, "errors": 0}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(worker_delete_addresses, url, api): url for url in target_urls}
        for future in as_completed(futures):
            try:
                url, result, deleted = future.result()
                if result == "success":
                    stats["success_accounts"] += 1
                    stats["total_deleted_addresses"] += deleted
                else:
                    stats["errors"] += 1
            except Exception:
                stats["errors"] += 1
    return stats, api.request_logs


# --- 3. بررسی تخفیف‌ها ---
def worker_check_discount(target_url, api):
    time.sleep(random.uniform(0.1, 1.0))
    data = fetch_data(target_url)
    if not data: return target_url, 0, "error_fetch"
    
    acc_token, ref_token = get_tokens_from_data(data)
    if not acc_token: return target_url, 0, "error_token"
    
    uid = get_user_id_from_token(acc_token)
    if not uid or uid == 0: return target_url, 0, "error_uuid"

    status, res = api.get_discounts(acc_token, uid)
    if status == 401 and ref_token:
        new_acc, _ = api.refresh_token(ref_token)
        if new_acc:
            acc_token = new_acc
            status, res = api.get_discounts(acc_token, uid)

    if status == 200 and isinstance(res, dict):
        discounts = res.get('data', [])
        if not discounts: return target_url, 0, "success"
        valid_amounts = [d.get('discountAmount', 0) for d in discounts if d.get('discountAmount')]
        max_d = max(valid_amounts) if valid_amounts else 0
        return target_url, max_d, "success"
    elif status == 401:
        return target_url, 0, "expired"
    else:
        return target_url, 0, "error_api"

def process_discount_links(session_dir, urls):
    api = OkalaAPI()
    stats = {"total": len(urls), "with_discount": 0, "no_discount": 0, "errors": 0}
    discounted_links = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(worker_check_discount, url, api): url for url in urls}
        for future in as_completed(futures):
            try:
                url, max_d, res = future.result()
                if res == "success":
                    if max_d > 0:
                        stats["with_discount"] += 1
                        discounted_links.append((url, max_d))
                    else:
                        stats["no_discount"] += 1
                else:
                    stats["errors"] += 1
            except Exception:
                stats["errors"] += 1

    report_file = None
    if discounted_links:
        report_file = os.path.join(session_dir, "Discounted_Links_Report.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("گزارش لینک‌های دارای تخفیف:\n" + "="*40 + "\n\n")
            # ❌ مشکل برطرف شد: چاپ آدرس لینک‌ها در خط جداگانه برای کپی آسان کاربر
            for url, amount in sorted(discounted_links, key=lambda x: x[1], reverse=True):
                f.write(f"🎁 تخفیف {int(amount/10000)} هزار تومانی:\n{url}\n\n")
                
    return stats, report_file, api.request_logs


# ==========================================
# هندلرهای تلگرام
# ==========================================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "سیستم چندمنظوره فعال است.\n\n"
        "لطفاً از منوی زیر یک گزینه را انتخاب کنید:\n"
        "(برای تمام بخش‌ها می‌توانید لینک‌ها را پیام کنید یا در فایل .txt بفرستید)",
        reply_markup=main_keyboard
    )

@router.message(F.text == "🛒 همگام‌سازی سبد خرید")
async def btn_sync_cart(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_sync_links)
    await message.answer("🛒 **همگام‌سازی سبد خرید**\n\nلطفاً لینک‌ها را متنی ارسال کنید یا یک فایل `.txt` شامل لینک‌ها بفرستید (لینک اول به عنوان الگو در نظر گرفته می‌شود).")

@router.message(F.text == "🗑 پاک کردن آدرس‌ها")
async def btn_delete_addresses(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_delete_links)
    await message.answer("🗑 **پاک کردن آدرس‌ها**\n\nلطفاً لینک‌ها را ارسال کنید یا یک فایل `.txt` حاوی لینک‌ها آپلود کنید.")

@router.message(F.text == "🔎 بررسی تخفیف‌ها")
async def btn_check_discounts(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_discount_links)
    await message.answer("🔎 **بررسی تخفیف‌ها**\n\nلطفاً لینک‌ها را ارسال کنید یا یک فایل `.txt` شامل لینک‌ها آپلود کنید.\nلینک‌های تخفیف‌دار در فایل متنی جداگانه به شما تحویل داده می‌شوند.")

# ----------- هندلر وضعیت همگام سازی -----------
@router.message(BotStates.waiting_for_sync_links, F.text | F.document)
async def handle_sync_links(message: Message, bot: Bot, state: FSMContext):
    urls = await extract_urls_from_message(message, bot)
    if len(urls) < 2:
        await message.answer("خطا: لطفاً حداقل ۲ لینک (یک الگو و حداقل یک هدف) در پیام یا فایل ارسال کنید.")
        return

    msg = await message.answer(f"در حال پردازش...\nاکانت مرجع دریافت شد. تعداد اهداف: {len(urls)-1}")
    session_dir = os.path.join(SESSION_BASE_DIR, str(uuid.uuid4()))
    os.makedirs(session_dir, exist_ok=True)
    
    result_data, logs, err = await asyncio.to_thread(process_all_links, session_dir, urls[0], urls[1:])

    if err:
        await msg.edit_text(err)
        shutil.rmtree(session_dir, ignore_errors=True)
        await state.clear()
        return

    final_zip_path, template_data, stats, error_file_path = result_data
    total_qty = sum(item['quantity'] for item in template_data['items'])

    report = (
        "✅ گزارش همگام‌سازی:\n\n"
        f"تعداد اقلام مرجع: {len(template_data['items'])} (مجموع: {total_qty} عدد)\n"
        f"🟢 موفق: {stats['success']} | 🔴 خطا: {stats['error_fetch'] + stats['error_address'] + stats['error_cart']}"
    )

    await msg.delete()
    await message.answer_document(document=FSInputFile(final_zip_path), caption=report)
    
    if error_file_path and os.path.exists(error_file_path):
        await message.answer_document(document=FSInputFile(error_file_path), caption="⚠️ فایل گزارش دقیق خطاهای سرور (Server Errors)")
        
    shutil.rmtree(session_dir, ignore_errors=True)
    await state.clear()

# ----------- هندلر وضعیت حذف آدرس -----------
@router.message(BotStates.waiting_for_delete_links, F.text | F.document)
async def handle_delete_links(message: Message, bot: Bot, state: FSMContext):
    urls = await extract_urls_from_message(message, bot)
    if not urls:
        await message.answer("خطا: هیچ لینکی یافت نشد.")
        return

    msg = await message.answer(f"در حال پردازش برای حذف آدرس...\nتعداد اکانت‌ها: {len(urls)}")
    session_dir = os.path.join(SESSION_BASE_DIR, str(uuid.uuid4()))
    os.makedirs(session_dir, exist_ok=True)
    
    stats, logs = await asyncio.to_thread(process_delete_all_links, session_dir, urls)

    await msg.delete()
    report = (
        "✅ گزارش حذف آدرس:\n\n"
        f"تعداد کل اکانت‌ها: {stats['total_targets']}\n"
        f"🟢 موفق: {stats['success_accounts']}\n"
        f"🗑 آدرس‌های حذف شده: {stats['total_deleted_addresses']}\n"
        f"🔴 خطا: {stats['errors']}"
    )
    await message.answer(report)
    shutil.rmtree(session_dir, ignore_errors=True)
    await state.clear()

# ----------- هندلر وضعیت بررسی تخفیف -----------
@router.message(BotStates.waiting_for_discount_links, F.text | F.document)
async def handle_discount_links(message: Message, bot: Bot, state: FSMContext):
    urls = await extract_urls_from_message(message, bot)
    if not urls:
        await message.answer("خطا: هیچ لینکی یافت نشد.")
        return

    msg = await message.answer(f"🔎 در حال بررسی تخفیف‌ها...\nتعداد لینک‌ها: {len(urls)}")
    session_dir = os.path.join(SESSION_BASE_DIR, str(uuid.uuid4()))
    os.makedirs(session_dir, exist_ok=True)
    
    stats, report_file, logs = await asyncio.to_thread(process_discount_links, session_dir, urls)

    await msg.delete()
    report = (
        "📊 گزارش بررسی تخفیف‌ها:\n\n"
        f"کل لینک‌ها: {stats['total']}\n"
        f"🎁 دارای تخفیف: {stats['with_discount']}\n"
        f"➖ بدون تخفیف/سوخته: {stats['no_discount']}\n"
        f"🔴 خطا: {stats['errors']}"
    )
    await message.answer(report)
    
    if report_file and os.path.exists(report_file):
        await message.answer_document(
            document=FSInputFile(report_file), 
            caption="🎁 فایل لینک‌های دارای تخفیف"
        )
    
    shutil.rmtree(session_dir, ignore_errors=True)
    await state.clear()

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
