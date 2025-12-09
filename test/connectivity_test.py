#!/usr/bin/env python3
"""Bedrock 连通性测试"""

import os
import boto3
import json
import sys
import time

# 配置 CloudFront 端点
# 部署后请将此处替换为你的 CloudFront 域名，例如 https://aabbccdd.cloudfront.net
CLOUDFRONT_ENDPOINT = "https://<YOUR_CLOUDFRONT_DOMAIN>"

# 测试模型列表（按区域）
TEST_MODELS = {
    'us-west-2': [
        {
            "id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "name": "Claude 3.5 Sonnet"
        },
        {
            "id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "name": "Claude Sonnet 4.5"
        }
    ],
    'us-east-1': [
        {
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "name": "Claude 3 Haiku"
        }
    ],
    'ap-northeast-1': [
        {
            "id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "name": "Claude 3.5 Sonnet"
        }
    ],
    'eu-west-1': [
        {
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "name": "Claude 3 Haiku"
        }
    ]
}

def test_connection(region, model_info, use_proxy=True, verbose=False):
    """测试连接"""
    # 设置端点
    if use_proxy:
        os.environ['AWS_ENDPOINT_URL_BEDROCK_RUNTIME'] = CLOUDFRONT_ENDPOINT
    else:
        os.environ.pop('AWS_ENDPOINT_URL_BEDROCK_RUNTIME', None)
    
    if verbose:
        endpoint_type = "代理" if use_proxy else "直连"
        print(f"  [{endpoint_type}] 测试 {model_info['name']} @ {region}...", end=" ", flush=True)
    
    try:
        # 创建客户端
        client = boto3.client('bedrock-runtime', region_name=region)
        
        # 准备请求
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        # 发送请求
        start_time = time.time()
        response = client.invoke_model(
            modelId=model_info['id'],
            body=json.dumps(body)
        )
        elapsed = time.time() - start_time
        
        # 解析响应
        result = json.loads(response['body'].read())
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        response_text = result['content'][0]['text']
        
        if verbose:
            print(f"OK ({elapsed:.2f}s)")
            print(f"      响应: {response_text[:80]}{'...' if len(response_text) > 80 else ''}")
            print(f"      Token: 输入={result['usage']['input_tokens']}, 输出={result['usage']['output_tokens']}")
        
        return {
            'success': True,
            'status_code': status_code,
            'elapsed': elapsed,
            'tokens': result['usage'],
            'response': response_text
        }
        
    except Exception as e:
        error_msg = str(e)
        if verbose:
            print(f"FAIL ({type(e).__name__})")
            print(f"      错误: {error_msg}")
        
        return {
            'success': False,
            'error_type': type(e).__name__,
            'error_msg': error_msg
        }

def print_header():
    """打印表头"""
    print("\n{:<30} {:<20} {:<5} {:<5} {:<5}".format(
        "模型", "区域", "直连", "代理", "响应时间"
    ))
    print("-" * 85)

def print_result(model_name, region, direct_result, proxy_result):
    """打印单行结果"""
    # 直连状态
    if direct_result['success']:
        direct_status = "OK"
    else:
        direct_status = "FAIL"
    
    # 代理状态
    if proxy_result['success']:
        proxy_status = "OK"
    else:
        proxy_status = "FAIL"
    
    # 响应时间（只显示代理的）
    if proxy_result['success']:
        elapsed = f"{proxy_result['elapsed']:.2f}s"
    else:
        elapsed = "-"
    
    print("{:<30} {:<20} {:<10} {:<10} {:<12}".format(
        model_name[:29],
        region,
        direct_status,
        proxy_status,
        elapsed
    ))

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                      Bedrock CloudFront 代理连通性测试                         ║
╚════════════════════════════════════════════════════════════════════════════════╝
""")
    print(f"CloudFront 端点: {CLOUDFRONT_ENDPOINT}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试区域列表
    regions = ['us-west-2', 'us-east-1', 'ap-northeast-1', 'eu-west-1']
    
    results = {
        'direct': {},
        'proxy': {}
    }
    
    # 执行测试
    print("\n正在执行测试...")
    print("="*85)
    
    test_count = 0
    for region in regions:
        if region in TEST_MODELS:
            for model in TEST_MODELS[region]:
                test_count += 1
                print(f"\n[{test_count}] {model['name']} @ {region}")
                
                key = f"{model['name']} @ {region}"
                
                # 测试直连
                direct_result = test_connection(region, model, use_proxy=False, verbose=True)
                results['direct'][key] = direct_result
                
                time.sleep(0.3)
                
                # 测试代理
                proxy_result = test_connection(region, model, use_proxy=True, verbose=True)
                results['proxy'][key] = proxy_result
                
                time.sleep(0.3)
    
    # 打印结果表格
    print_header()
    
    for region in regions:
        if region in TEST_MODELS:
            for model in TEST_MODELS[region]:
                key = f"{model['name']} @ {region}"
                print_result(model['name'], region, results['direct'][key], results['proxy'][key])
    
    # 统计汇总
    print("\n" + "="*85)
    print("测试汇总")
    print("="*85)
    
    direct_success = sum(1 for r in results['direct'].values() if r['success'])
    proxy_success = sum(1 for r in results['proxy'].values() if r['success'])
    total = len(results['direct'])
    
    print(f"\n直连 Bedrock API:")
    print(f"  成功: {direct_success}/{total}")
    print(f"  失败: {total - direct_success}/{total}")
    print(f"  成功率: {direct_success/total*100:.0f}%")
    
    print(f"\nCloudFront 代理:")
    print(f"  成功: {proxy_success}/{total}")
    print(f"  失败: {total - proxy_success}/{total}")
    print(f"  成功率: {proxy_success/total*100:.0f}%")
    
    # 失败详情
    direct_failures = [k for k, v in results['direct'].items() if not v['success']]
    proxy_failures = [k for k, v in results['proxy'].items() if not v['success']]
    

if __name__ == "__main__":
    sys.exit(main())
