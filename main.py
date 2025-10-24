from app.services import DNSService
from app.services import IPService

def main():
    dns_service = DNSService()
    dns_info = dns_service.get_dns_info("www.hytch.com")
    print(dns_info.model_dump_json(indent=4, exclude={"query_time"}))
    ip_service = IPService()
    ip_info = ip_service.get_ip_info("8.8.8.8")
    print(ip_info.model_dump_json(indent=4, exclude={"query_time"}))


if __name__ == "__main__":
    main()
