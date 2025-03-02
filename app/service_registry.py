from socket import gethostname, gethostbyname  # 明确导入

import consul

# Consul 客户端和服务信息
consul_client = None
service_id = None


def register_service_with_consul():
    global consul_client, service_id
    # 获取本机IP地址
    hostname = gethostname()
    ip_address = gethostbyname(hostname)

    # Consul 客户端
    consul_client = consul.Consul()

    # 服务注册信息
    service_id = f'trading-plus-{ip_address}'
    service_name = 'trading-plus'
    service_port = 5000

    # 注册服务
    consul_client.agent.service.register(
        service_name,
        service_id=service_id,
        address=ip_address,
        port=service_port,
        check={
            "name": "HTTP Check",
            "http": f"http://{ip_address}:{service_port}/actuator/health",
            "interval": "10s",
            "timeout": "5s"
        }
    )
    print(f"Service registered with Consul: {service_id}")


def deregister_service_with_consul():
    """注销 Consul 实例"""
    global consul_client, service_id
    if consul_client and service_id:
        try:
            consul_client.agent.service.deregister(service_id)
            print(f"Service deregistered from Consul: {service_id}")
        except Exception as e:
            print(f"Failed to deregister service from Consul: {e}")
