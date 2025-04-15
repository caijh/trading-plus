import requests


def http_get_with_retries(url, max_retries=3, default_return_value=None):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            data = response.json()
            # 检查返回的数据中状态码是否为0，表示请求成功
            if data['code'] == 0:
                # 如果请求成功，返回数据中的data
                return data['data']
        except requests.RequestException as e:
            print(f'请求失败，尝试 {attempt + 1}/{max_retries}: {e}')
    return default_return_value
