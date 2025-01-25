def is_in_range(char, start, end):
    """检查字符是否在指定范围内"""
    return start <= char <= end

def filter_domains(input_file, start_char, end_char):
    """
    根据指定的字符范围筛选域名
    
    Args:
        input_file: 输入文件路径
        start_char: 范围起始字符 (可以是数字或字母)
        end_char: 范围结束字符 (可以是数字或字母)
    """
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    filtered_domains = []
    for line in lines:
        line = line.strip()
        if line.strip().endswith('.xyz'):
            prefix = line.strip()[:-4]  # remove .xyz
            # 检查是否所有字符都在指定范围内
            if all(is_in_range(c, start_char, end_char) for c in prefix):
                filtered_domains.append(line.strip())
    
    return filtered_domains

if __name__ == "__main__":
    input_file = "domains_log/available_domains_20250123_120518.txt"
    
    # 示例：筛选5-7之间的域名
    start = '0'
    end = '4'
    domains = filter_domains(input_file, start, end)
    
    print(f"Domains with all characters between {start} and {end}:")
    print("=" * 40)
    for domain in sorted(domains):
        print(domain)
    
    # 使用示例:
    # 数字区间: start='4', end='6'
    # 字母区间: start='a', end='d'
    # 注意：start和end必须是同类型（都是数字或都是字母）
