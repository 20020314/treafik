import requests
import time

# 钱包地址
wallet_address = "43p8AgGKbhH198j4aTvwMb42PwT6Mc1qzYm7Bxg4y4DTESJtGAvzgGePtwqudFmz7RCi29fwkuG4ZLgxmmQzN8joADCEv9S"

# pushdeer的URL
push_url = "http://pushdeer.pushdeer.svc.cluster.local/message/push"

# 您的PushKey
push_key = "PDU1TpP6ANbDAVtPLtqnUUvNgDykCMm6dTc8d"

def get_miner_stats(wallet_address):
    url = f"https://supportxmr.com/api/miner/{wallet_address}/stats"
    response = requests.get(url)
    data = response.json()
    xmr_amount = data["amtDue"] / 1000000000000  # 将XMR数量换算为XMR
    hashrate = data["hash"] / 1000  # 将算力换算为KH/s
    valid_shares = data["validShares"]
    invalid_shares = data["invalidShares"]
    return xmr_amount, hashrate, valid_shares, invalid_shares

def push_message(message):
    data = {
        "pushkey": push_key,
        "text": message,
        "type": "markdown"
    }
    response = requests.post(push_url, data=data)
    if response.status_code != 200:
        print(f"推送消息失败: {response.text}")

def calculate_earnings(xmr_amount):
    url = f'https://vip-api.changenow.io/v1.6/exchange/estimate?fromCurrency=xmr&fromNetwork=xmr&fromAmount={xmr_amount:.2f}&toCurrency=usdt&toNetwork=trx&type=direct&promoCode=&withoutFee=false'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    estimated_amount_usd = data["summary"]["estimatedAmount"]

    rate_url = "https://currencies.2miners.com/api/v1/local/cny"
    response = requests.get(rate_url)
    data = response.json()
    rate = float(data["rate"])

    daily_earnings_cny = estimated_amount_usd * rate
    return daily_earnings_cny, estimated_amount_usd

current_xmr_amount, current_hashrate, current_valid_shares, current_invalid_shares = get_miner_stats(wallet_address)
print(f"初始XMR数量: {current_xmr_amount:.8f}, 初始算力: {current_hashrate:.2f} KH/s, validShares: {current_valid_shares}, invalidShares: {current_invalid_shares}")

# 初始推送消息
push_message(f"初始XMR数量: {current_xmr_amount:.8f}\n初始算力: {current_hashrate:.2f} KH/s\n有效Shares: {current_valid_shares}\n拒绝Shares: {current_invalid_shares}")

# 初始化变量
start_time = time.time()
total_hashrate = current_hashrate
total_valid_shares = current_valid_shares
total_invalid_shares = current_invalid_shares
count = 1

while True:
    time.sleep(60)  # 每60秒检查一次算力

    new_xmr_amount, new_hashrate, new_valid_shares, new_invalid_shares = get_miner_stats(wallet_address)
    if new_hashrate > current_hashrate * 1.2 or new_hashrate < current_hashrate * 0.8:
        message = f"算力波动超过20%!\n当前算力: {new_hashrate:.2f} KH/s\n当前XMR数量: {new_xmr_amount:.8f}\n有效Shares: {new_valid_shares}\n拒绝Shares: {new_invalid_shares}"
        push_message(message)
        print(message)
        current_hashrate = new_hashrate

    count += 1
    total_hashrate += new_hashrate
    total_valid_shares += new_valid_shares
    total_invalid_shares += new_invalid_shares
    elapsed_time = time.time() - start_time
    if elapsed_time >= 600:  # 每10分钟推送一次当前算力和平均算力以及收益信息
        average_hashrate = total_hashrate / count
        average_valid_shares = int(total_valid_shares / count)  # 取整数部分
        average_invalid_shares = int(total_invalid_shares / count)  # 取整数部分
        daily_earnings_cny, estimated_amount_usd = calculate_earnings(new_xmr_amount)
        push_message(f"当前算力: {new_hashrate:.2f} KH/s\n平均算力: {average_hashrate:.2f} KH/s\n当前XMR数量: {new_xmr_amount:.8f}\n有效Shares: {average_valid_shares}\n拒绝Shares: {average_invalid_shares}\n当前收益（CNY）: {daily_earnings_cny:.2f}  当前收益（USDT）: {estimated_amount_usd:.2f}")
        start_time = time.time()
        total_hashrate = new_hashrate
        total_valid_shares = new_valid_shares
        total_invalid_shares = new_invalid_shares
        count = 1
