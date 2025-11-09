from app.services.dns_service import DNSService
from app.services.ip_service import IPService
from app.services.web_search_service import WebSearchService
import asyncio

async def main():
    dns_service = DNSService()
    ip_service = IPService()
    web_search_service = WebSearchService()
    dns_info = await dns_service.get_dns_info("www.example.com")
    print(dns_info.model_dump_json(indent=4))
    ip_info = await ip_service.get_ip_info("8.8.8.8")
    print(ip_info.model_dump_json(indent=4))
    web_search_info =await web_search_service.search("example.com")
    print(web_search_info.model_dump_json(indent=4))

if __name__ == "__main__":
    asyncio.run(main())