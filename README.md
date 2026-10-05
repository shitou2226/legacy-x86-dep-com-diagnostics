# 旧版 x86 DEP 与虚拟串口诊断工具

这是一个去标识化、只包含原创内容的诊断仓库，用于：

- 只读查看 Windows PE 文件的架构、入口点和节区权限；
- 理解旧版 x86 程序在现代 Windows DEP 保护下发生取指异常的诊断思路；
- 在确认两端均为测试用虚拟串口后，执行受控的串口回环验证。

## 合规边界

本仓库不包含、也不接受：

- 任何第三方 EXE、DLL、SYS、CAT、INF、MSI、CHM 或安装包；
- 修改后的商业软件、汉化资源、驱动、原始文件备份或二进制差分；
- 破解、激活、授权绕过、密钥、授权标记或针对具体商业产品的补丁；
- 反汇编转储、固定偏移、产品专用哈希、本机绝对路径或个人身份信息。

仓库中的工具不会修改被检查的 PE 文件。对于不拥有源代码或没有书面修改授权的软件，应联系软件厂商获取兼容版本或许可支持。

## 使用方法

### 1. 只读检查 PE 节区

```powershell
python tools/inspect_pe_sections.py "sample-authorized-file.exe"
python tools/inspect_pe_sections.py "sample-authorized-file.dll" --json
```

输出包括 PE32/PE32+、目标架构、入口点 RVA，以及各节区的读、写、执行权限。工具只读取输入文件，不写回任何字节。

### 2. 虚拟串口回环测试

先安装依赖：

```powershell
python -m pip install -r requirements.txt
```

确认两个端口是专用测试端口并互相连接后运行：

```powershell
python tools/com_loopback_test.py --tx COM10 --rx COM11 --confirm-test-ports
```

不要把该命令用于生产设备、真实 PLC、变频器或其他可能响应串口数据的硬件。

## 验证

```powershell
python -m unittest discover -s tests -v
python tools/release_audit.py .
```

## 参考资料

- [Microsoft：PE/COFF 文件格式](https://learn.microsoft.com/windows/win32/debug/pe-format)
- [Microsoft：Exploit protection 中的 DEP 说明](https://learn.microsoft.com/defender-endpoint/exploit-protection-reference#data-execution-prevention-dep)

## 许可证

本仓库原创代码和文档采用 MIT License。该许可证不授予任何第三方软件、商标、驱动或二进制文件的权利。
