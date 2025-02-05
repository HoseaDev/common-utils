import base64
import json
import sys

def decode_vmess_url(vmess_url):
    """解码vmess URL并返回配置字典"""
    if not vmess_url.startswith('vmess://'):
        raise ValueError("Invalid vmess URL")
    
    # 移除 'vmess://' 前缀并解码base64
    encoded_config = vmess_url[8:]
    try:
        config_str = base64.b64decode(encoded_config).decode('utf-8')
        config = json.loads(config_str)
        return config
    except Exception as e:
        raise ValueError(f"Failed to decode vmess URL: {str(e)}")

def encode_vmess_url(config):
    """将配置字典编码为vmess URL"""
    config_str = json.dumps(config)
    encoded_config = base64.b64encode(config_str.encode('utf-8')).decode('utf-8')
    return f"vmess://{encoded_config}"

def display_config(config):
    """显示配置的详细信息"""
    # 输出config 所有字段
    print(f"{json.dumps(config, indent=4)}")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python vmess_converter.py <vmess_url>")
        sys.exit(1)

    vmess_url = sys.argv[1]
    
    try:
        # 解码并显示当前配置
        config = decode_vmess_url(vmess_url)
        display_config(config)
        
        # 获取用户输入的新IP和端口
        print("\n请输入新的配置 (直接回车保持原值):")
        new_ip = input(f"新IP地址 [{config['add']}]: ").strip()
        new_port = input(f"新端口 [{config['port']}]: ").strip()
        new_tls = input(f"TLS设置 (true/tls/false/none) [{config.get('tls', 'none')}]: ").strip().lower()
        
        # 更新配置
        if new_ip:
            config['add'] = new_ip
        if new_port:
            config['port'] = int(new_port)
        if new_tls:
            if new_tls in ['true', 'tls']:
                config['tls'] = 'tls'
            elif new_tls in ['false', 'none']:
                config['tls'] = 'none'
            else:
                print(f"警告: 无效的TLS设置 '{new_tls}'，将保持原值")
        
        # 显示更新后的配置
        print("\n更新后的配置:")
        display_config(config)
        
        # 生成新的vmess URL
        new_vmess_url = encode_vmess_url(config)
        print("\n新的vmess链接:")
        print(new_vmess_url)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()