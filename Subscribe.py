import os
import re
import sys
import json
from base64 import b64decode

import requests
import yaml

# 用于存储所有节点
all_nodes: list = []


def getNodes(url, retries=3) -> str | None:
    """通过订阅链接获取节点"""
    try:
        with requests.get(url) as response:
            if response.status_code == 200:
                return response.text
            else:
                if retries > 0:
                    getNodes(url, retries=retries - 1)
                else:
                    print(f"访问订阅地址出错！, HTTP status code: {response.status_code}")
                    return
    except Exception as e:
        print(e)


def decodeBase64(encrypt_string: str) -> str:
    """节点 base64 解密"""
    # 检查长度是否为 4 的倍数，如果不是，添加适当数量的 '=' 字符
    padding = '=' * (4 - len(encrypt_string) % 4)
    return b64decode(encrypt_string + padding).decode()


def isUseless(server: str) -> bool:
    """判断是否为无用节点"""
    # 定义正则表达式匹配有效的外网 IP 地址
    ip_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    # 检查 server 是否为有效的 IP 地址
    if re.match(ip_pattern, server):
        # 排除特殊地址
        private_ips = ('10.', '100.', '127.', '169.', '172.16.', '192.168.')
        if server.startswith(private_ips):
            return True
    elif server.isdigit():
        return True
    else:
        return False


def ss(node: str | dict[str, str]) -> None:
    """格式化 ss 节点"""
    if isinstance(node, str):
        extracted_node = re.findall(r'ss://(?P<cipher_and_password>.*?)@(?P<server>.*?):(?P<port>.*?)#', node)[0]

        server = extracted_node[1]
        if isUseless(server):
            return

        # 提取 cipher 和 password 以及端口
        cipher_and_password = decodeBase64(extracted_node[0])
        cipher, password = cipher_and_password.split(":")
        port = extracted_node[2]

        all_nodes.append(f"forward=ss://{cipher}:{password}@{server}:{port}")
        return

    elif isinstance(node, dict):
        if isUseless(node['server']):
            return
        try:
            all_nodes.append(f"forward=ss://{node['cipher']}:{node['password']}@{node['server']}:{node['port']}")
        except KeyError as e:
            print(e)
            return


def vmess(node: str | dict[str, str]) -> None:
    """格式化 vmess 节点"""
    if isinstance(node, str):
        # 从节点中移除 "vmess://" 前缀，并去除任何前导或尾随的空格。
        encrypt_vmess = node.strip().replace("vmess://", "")

        # 使用 base64 解码来解密 vmess 节点。
        decrypt_vmess = decodeBase64(encrypt_vmess)

        # 将解密的 vmess 节点转换为 JSON 对象，提取 uuid、服务器和端口
        vmess_json = json.loads(decrypt_vmess)

        server = vmess_json["add"]
        if isUseless(server):
            return

        uuid = vmess_json["id"]
        port = vmess_json["port"]

        all_nodes.append(f"forward=vmess://{uuid}@{server}:{port}")
        return
    elif isinstance(node, dict):
        if isUseless(node['server']):
            return
        try:
            all_nodes.append(f"forward=vmess://{node['uuid']}@{node['server']}:{node['port']}")
        except KeyError as e:
            print(e)
            return


def trojan(node: str | dict[str, str]) -> None:
    """格式化 trojan 节点"""
    if isinstance(node, str):
        # 使用正则表达式从节点中提取出密码、服务器和端口
        extracted = re.findall(r'trojan://(.*?)@(.*?):(.*?)\?allowInsecure=(\d).*?&sni=(.*?)#', node)[0]

        server = extracted[1]
        if isUseless(server):
            return
        password = extracted[0]
        port = extracted[2]
        skip_verify = "true" if extracted[3] == "1" else "false"
        server_name = extracted[4]

        all_nodes.append(
            f"forward=trojan://{password}@{server}:{port}?servername={server_name}&skipVerify={skip_verify}")
        return
    elif isinstance(node, dict):
        if isUseless(node['server']):
            return
        skip_verify = node.get("skip-cert-verify", "false")
        try:
            all_nodes.append(
                f"forward=trojan://{node['password']}@{node['server']}:{node['port']}?servername={node['sni']}&skipVerify={skip_verify}")
        except KeyError as e:
            print(e)
            return


def processNodes(nodes: str | list[dict[str, str]]) -> None:
    """处理节点"""
    SUPPORT_PROTOCOLS = ("ss", "vmess", "trojan")
    if isinstance(nodes, str):
        for node in nodes.split('\r'):
            node = node.strip()
            for protocol in SUPPORT_PROTOCOLS:
                if node.startswith(protocol):
                    globals()[protocol](node)
    elif isinstance(nodes, list):
        for node in nodes:
            protocol = node.get("type")
            if protocol in SUPPORT_PROTOCOLS:
                globals()[protocol](node)
            else:
                print(f"不支持的协议类型: {protocol}")
    else:
        print("节点类型错误！")


def getNodesFromYaml() -> None:
    """获取当前路径所有 yaml 文件中的节点"""
    files = [file for file in os.listdir() if file.endswith(".yaml")]

    if not files:
        print("当前路径下没有 yaml 文件")
        return

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            nodes = yaml.safe_load(f)["proxies"]
        processNodes(nodes)


def addSubscribe(url: str) -> None:
    """将订阅地址添加到 subscribes.txt 文件中"""
    filename = "subscribes.txt"
    if not os.path.isfile(filename):
        filename = "Subscribes.txt"
    subscribe = getSubscribes()
    if subscribe and url in subscribe:
        return
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(url + "\n")


def getSubscribes() -> list[str] | None:
    """获取 subscribes.txt 文件中的订阅地址"""
    filename = "subscribes.txt"
    if not os.path.isfile(filename):
        filename = "Subscribes.txt"
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            subscribes = [line.strip() for line in file if line.strip().startswith("http")]
            return subscribes
    except FileNotFoundError:
        return


def main():
    if len(sys.argv) > 1 and not sys.argv[0].endswith('.py'):
        print("正在获取订阅链接中的节点...")
        url = sys.argv[1]
        encrypt_nodes = getNodes(url)
        if encrypt_nodes is not None and encrypt_nodes != "":
            addSubscribe(url)
            nodes = decodeBase64(encrypt_nodes)
            processNodes(nodes)
        else:
            exit()
    else:
        subscribes = getSubscribes()
        if subscribes is not None and subscribes != []:
            print("正在通过 subscribes.txt 文件中的订阅地址获取节点...")
            for subscribe in subscribes:
                encrypt_nodes = getNodes(subscribe)
                if encrypt_nodes is not None and encrypt_nodes != "":
                    nodes = decodeBase64(encrypt_nodes)
                    processNodes(nodes)
                else:
                    continue
        else:
            print("正在获取当前路径下所有 yaml 文件中的节点...")
            getNodesFromYaml()

    if all_nodes:
        with open("forward.txt", "w", encoding="utf-8") as file:
            for node in all_nodes:
                file.write(node.strip() + "\n")
        print("已将节点写入 forward.txt 文件")
    else:
        exit()


if __name__ == '__main__':
    main()
