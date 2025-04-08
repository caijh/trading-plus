import consul

from environment.service import env_vars

# Consul 客户端和服务信息
consul_client = None
service_id = None


def register_service_with_consul():
    global consul_client, service_id
    # 获取本机IP地址
    ip_address = env_vars.APPLICATION_CLOUD_DISCOVERY_HOST_IP

    # Consul 客户端
    consul_host = env_vars.APPLICATION_CLOUD_DISCOVERY_SERVER_HOST
    consul_port = env_vars.APPLICATION_CLOUD_DISCOVERY_SERVER_PORT
    consul_token = env_vars.APPLICATION_CLOUD_DISCOVERY_SERVER_TOKEN
    consul_schema = 'http'
    if consul_port == 443:
        consul_schema = 'https'
    consul_client = consul.Consul(scheme=consul_schema, host=consul_host, port=consul_port, token=consul_token)

    # 服务注册信息
    service_name = 'trading-plus'
    service_id = f'{service_name}@{ip_address}'
    service_port = int(env_vars.APPLICATION_CLOUD_DISCOVERY_HOST_PORT)
    service_schema = 'http'
    if service_port == 443:
        service_schema = 'https'

    # 注册服务
    consul_client.agent.service.register(
        service_name,
        service_id=service_id,
        address=ip_address,
        port=service_port,
        token=consul_token,
        check={
            "name": "HTTP Check",
            "http": f"{service_schema}://{ip_address}:{service_port}/actuator/health",
            "interval": "30s",
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
