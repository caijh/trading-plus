from consul import Consul
from fastapi import APIRouter

from app.core.env import CONSUL_PORT, CONSUL_HOST, CONSUL_TOKEN, SERVICE_NAME, SERVICE_HOST, \
    SERVICE_PORT


def get_consul_server():
    scheme = 'http'
    if CONSUL_PORT == 443:
        scheme = 'https'
    return Consul(scheme=scheme, host=CONSUL_HOST, port=CONSUL_PORT, token=CONSUL_TOKEN)


# 注册到 Consul的函数
def register_service():
    consul = get_consul_server()
    service_id = f"{SERVICE_NAME}@{SERVICE_HOST}"
    service_address = SERVICE_HOST

    service_schema = 'http'
    if SERVICE_PORT == 443:
        service_schema = 'https'

    # 服务注册
    consul.agent.service.register(
        SERVICE_NAME,
        service_id=service_id,
        port=SERVICE_PORT,
        address=service_address,
        tags=["trading"],  # 可根据需要自定义tags
        token=CONSUL_TOKEN,
        check={
            "name": "HTTP Check",
            "http": f"{service_schema}://{service_address}:{SERVICE_PORT}/actuator/health",  # 健康检查URL
            "timeout": "5s",
            "interval": "30s"
        }
    )
    print(f"Service {SERVICE_NAME} registered with Consul at {service_address}:{SERVICE_PORT}")


# 注销服务
def deregister_service():
    consul = get_consul_server()
    service_id = f"{SERVICE_NAME}@{SERVICE_HOST}"

    # 服务注销
    consul.agent.service.deregister(service_id)
    print(f"Service {SERVICE_NAME} deregistered from Consul")


actuator_router = APIRouter()


@actuator_router.get("/health")
def health_check():
    return {"status": "healthy"}
