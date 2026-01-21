import requests
import os
import sys
from dotenv import load_dotenv

def test_twitter_token(token: str):
    """验证 Twitter Bearer Token 是否可用，支持代理"""
    print(f"开始验证 Token: {token[:20]}...{token[-10:]}")
    
    url = "https://api.twitter.com/2/users/by/username/Twitter"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "TokenValidator"
    }
    
    # 尝试从环境变量获取代理配置
    proxies = {}
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
        
    if proxies:
        print(f"检测到代理配置: {proxies}")
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 验证成功！")
            print(f"数据反馈: {data.get('data', {}).get('name')} (@{data.get('data', {}).get('username')})")
            return True
        elif response.status_code == 401:
            print("❌ 验证失败: 401 Unauthorized (Token 无效或已过期)")
        elif response.status_code == 403:
            print("❌ 验证失败: 403 Forbidden (权限不足，请确认已在 Developer Portal 开启权限)")
        elif response.status_code == 429:
            print("⚠️ 验证失败: 429 Too Many Requests (该 Token 已被限流)")
        else:
            print(f"❓ 验证失败: HTTP {response.status_code}")
            print(response.text)
            
        return False
    except Exception as e:
        print(f"💥 请求过程中发生错误: {e}")
        print("\n[提示] 如果你在国内，请确保在 .env 中正确配置了代理（HTTP_PROXY/HTTPS_PROXY）或者开启了系统全局代理。")
        return False

if __name__ == "__main__":
    # 加载 .env
    load_dotenv()
    
    # 获取 Token
    env_token = os.getenv("TWITTER_BEARER_TOKEN")
    manual_token = "AAAAAAAAAAAAAAAAAAAAAP1r3AEAAAAAzwE8GwAk3hxZmc2Gizlu4%2FQBvAQ%3D2y5WX0ZwxeBZdinSLGbPtybAg29rdDwiMbUGgIcdOzmJ62CIHe"
    
    # 优先使用 .env 里的，方便批量测试
    target_token = env_token if env_token else manual_token
    
    if not target_token or "你的_" in target_token:
        print("错误: 未找到可测试的 Token，请在 .env 中填写。")
        sys.exit(1)
        
    tokens_to_test = target_token.split(',')
    
    for t in tokens_to_test:
        test_twitter_token(t.strip())
        print("-" * 40)
