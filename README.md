# Glider Forward Format

## 简介

由于渗透测试、网络防御以及网络爬虫的需求，常常被封 IP，IP 代理池又太贵，但是刚好有机场代理，为了高效地管理和使用这些节点，需要一个上游代理工具来有效地整合它们。这个 Python 脚本的目标是从订阅链接或 YAML 文件中获取节点，并生成适用于 **Gilder**[^1] 项目的配置文件。

## 功能特点

- 从订阅链接或 YAML 文件中获取节点。
- 暂时只支持 Shadowsocks（ss）、V2Ray（vmess）和 Trojan（trojan）协议。
- 自动解密和处理加密的节点信息。
- 生成的 `forward.txt` 文件包含格式化的节点信息

## 使用方法

### 运行脚本

#### 从 `forward.txt` 里的订阅地址或 YAML 文件中获取节点

脚本会首先尝试读取 `subscribe.txt` 文件。如果文件存在且不为空，它将从文件中获取订阅。如果文件不存在或为空，它将从当前目录下的所有 yaml 文件中获取节点。

```
python Subscribe.py
```

#### 从订阅链接获取节点

要从订阅链接生成配置文件，请运行以下命令：

```
python Subscribe.py https://your_subscription_link_here
```

将 `https://your_subscription_link_here` 替换为实际的订阅链接。每次运行脚本都会将订阅地址写入到 `subscribe.txt` 文件中，无需每次运行都添加订阅地址。
如果有多个订阅地址，可以将它们写入到 `subscribes.txt` 文件中，每行一个，然后运行脚本即可。

### 输出

Glider[^1] Forward 格式将保存为 `forward.txt`，位于项目目录中。

```
forward=trojan://cdf75afd-d72d-440b-a864-424ee636ee86@smus.aikunapp.com:443
forward=vmess://cdf75afd-d72d-440b-a864-424ee636ee86@kr.aikunapp.com:20006
forward=ss://chacha20-ietf-poly1305:b6312208-40c0-4752-baf5-996bee58cf87@jh.xianyuwangzhi.top:27211
```

## 要求

- Python 3.x
- requests
- pyyaml

[^1]: [GitHub - nadoo/glider: glider is a forward proxy with multiple protocols support, and also a dns/dhcp server with ipset management features(like dnsmasq).](https://github.com/nadoo/glider/tree/master)# Glider-Forward-Format
