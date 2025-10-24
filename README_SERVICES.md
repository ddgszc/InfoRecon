# DNS和IP信息查询服务

本项目提供了两个核心服务类，用于查询DNS记录和IP地址信息。

## 功能特性

### DNS服务 (DNSService)

查询域名的各类DNS记录：

- **A记录** - IPv4地址记录，将域名映射到IPv4地址
- **AAAA记录** - IPv6地址记录，将域名映射到IPv6地址
- **MX记录** - 邮件交换记录，指定接收电子邮件的邮件服务器
- **TXT记录** - 文本记录，用于SPF、DKIM、域名验证等
- **NS记录** - 域名服务器记录，指定域名解析服务器

### IP服务 (IPService)

查询IP地址的详细信息：

- **基本信息** - IP版本、是否私有IP
- **反向DNS** - 通过IP查询域名
- **地理位置** - 国家、地区、城市、经纬度、时区
- **ASN信息** - 自治系统号、ISP、组织信息

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install dnspython requests pydantic pydantic-settings
```

## 快速开始

### DNS查询示例

```python
from app.services import DNSService

# 创建DNS服务实例
dns_service = DNSService()

# 查询域名的所有DNS记录
dns_info = dns_service.get_dns_info("google.com")

# 访问A记录
for record in dns_info.a_records:
    print(f"{record.host} -> {record.ip}")

# 访问MX记录
for record in dns_info.mx_records:
    print(f"邮件服务器: {record.exchange}, 优先级: {record.priority}")

# 只查询特定类型的记录
a_records = dns_service.get_dns_info_by_type("google.com", "A")
```

### IP查询示例

```python
from app.services import IPService

# 创建IP服务实例
ip_service = IPService()

# 查询IP信息
ip_info = ip_service.get_ip_info("8.8.8.8")

# 访问地理位置信息
if ip_info.geo_location:
    print(f"国家: {ip_info.geo_location.country}")
    print(f"城市: {ip_info.geo_location.city}")

# 访问ASN信息
if ip_info.asn_info:
    print(f"ISP: {ip_info.asn_info.isp}")
    print(f"ASN: {ip_info.asn_info.asn}")

# 获取本机公网IP
my_ip = ip_service.get_my_ip()
print(f"本机IP: {my_ip}")

# 批量查询
ips = ["8.8.8.8", "1.1.1.1"]
results = ip_service.batch_get_ip_info(ips)
```

## 数据结构

### DNS数据结构

所有DNS数据结构定义在 `app/schema/dns_schema.py` 中：

- `ARecord` - A记录
- `AAAARecord` - AAAA记录
- `MXRecord` - MX记录
- `TXTRecord` - TXT记录
- `NSRecord` - NS记录
- `DNSInfo` - DNS信息汇总

### IP数据结构

所有IP数据结构定义在 `app/schema/ip_schema.py` 中：

- `GeoLocation` - 地理位置信息
- `ASNInfo` - ASN信息
- `IPInfo` - IP信息汇总

## 高级用法

### 自定义DNS服务器

```python
# 使用Google的公共DNS服务器
dns_service = DNSService(
    timeout=10.0,
    nameservers=['8.8.8.8', '8.8.4.4']
)
```

### 自定义超时时间

```python
# 设置5秒超时
ip_service = IPService(timeout=5.0)
```

### JSON序列化

所有数据模型都基于Pydantic，可以轻松转换为JSON：

```python
dns_info = dns_service.get_dns_info("example.com")

# 转换为字典
data_dict = dns_info.model_dump()

# 转换为JSON
import json
json_str = json.dumps(data_dict, indent=2, default=str, ensure_ascii=False)
print(json_str)
```

### 错误处理

服务会捕获异常并在返回的对象中包含错误信息：

```python
dns_info = dns_service.get_dns_info("invalid-domain-12345.com")
if dns_info.error:
    print(f"查询失败: {dns_info.error}")
```

## 运行示例

项目包含完整的示例代码：

```bash
python examples/test_services.py
```

## 注意事项

1. **IP地理位置API限制**
   - 使用免费的 ip-api.com 服务
   - 有请求频率限制（45次/分钟）
   - 对于生产环境，建议使用付费API或自建服务

2. **私有IP地址**
   - 私有IP（如192.168.x.x）不会查询地理位置和ASN信息
   - 私有IP范围：10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16

3. **DNS查询失败**
   - 如果某类记录不存在，返回空列表
   - 不会抛出异常，便于批量处理

4. **超时设置**
   - 默认超时5秒
   - 可根据网络环境调整

## 项目结构

```
InfoRecon/
├── app/
│   ├── schema/
│   │   ├── __init__.py
│   │   ├── dns_schema.py      # DNS数据模型
│   │   └── ip_schema.py       # IP数据模型
│   └── services/
│       ├── __init__.py
│       ├── dns_service.py     # DNS查询服务
│       └── ip_service.py      # IP查询服务
├── examples/
│   └── test_services.py       # 使用示例
├── requirements.txt           # 依赖包
└── README_SERVICES.md         # 本文档
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

