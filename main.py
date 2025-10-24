from app.services import DNSService

def main():
    dns_service = DNSService()
    dns_info = dns_service.get_dns_info("")
    print(dns_info.model_dump_json(indent=4, exclude={"query_time"}))


if __name__ == "__main__":
    main()
