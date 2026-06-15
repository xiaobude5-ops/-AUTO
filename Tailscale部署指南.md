# Tailscale 跨办公区部署指南

## 背景

几何星球AUTO 是网页服务，部署在一台电脑（服务器）上。
通过 Tailscale 免费虚拟局域网，其他办公区的员工无需公网 IP、无需端口映射，直接用浏览器访问。

## 一、服务器电脑 — 装 Tailscale（这台，一次）

1. 浏览器打开 https://tailscale.com/download/windows
2. 下载 `tailscale-setup-x.x.x.exe`，双击安装（一路下一步）
3. 安装完成 → 托盘出现 Tailscale 图标（黑色网格）
4. 右键托盘 → **Log in**
5. 跳转到浏览器，选 Google / Microsoft / GitHub 任意一种登录
6. 登录后托盘图标变蓝色 → 已连接
7. 右键托盘 → Tailscale → 查看 IP 地址，形如：

   ```
   ╔══════════════════════════╗
   ║ yion-desktop            ║
   ║ 100.64.1.5              ║    ← 把这个记下来
   ╚══════════════════════════╝
   ```

8. 员工访问地址是：`http://100.64.1.5:5150`（换成你的实际 IP）


## 二、员工电脑 — 装 Tailscale（每台电脑，也是只做一次）

### 方式 A：你在员工电脑操作（推荐，最简单）

1. 在员工电脑上同样装 Tailscale（上一步 1–4）
2. 登录时**用你同一个账号**（Google/Microsoft/GitHub 跟你的一致）
3. 登录后，浏览器访问：`http://你的TailscaleIP:5150`
4. 建议把地址加个书签

### 方式 B：员工自己操作

1. 把 `https://tailscale.com/download/windows` 发给员工
2. 员工装好 Tailscale 后，告诉你
3. 你打开 https://login.tailscale.com/admin/machines
4. 点右上角 **Share** → **Invite external users** → 填员工邮箱
5. 员工在 Tailscale 自己的账号登录，完成后只能在 `100.x.x.x` 访问你那台电脑
6. 把 `http://你的TailscaleIP:5150` 发给员工


## 三、验证

在任意一台已连 Tailscale 的电脑上：

```
ping 100.64.1.5          ← 换成你的 Tailscale IP，应能通
```

浏览器打开 `http://100.64.1.5:5150`，应能看到登录页。

## 四、常见问题

**Tailscale 连不上？**
- 确认两台电脑都能上网
- 托盘图标要是蓝色（不是黑色/灰色）
- 右键托盘 → Reconnect

**浏览器打不开？**
- 确认服务器电脑上 `启动.bat` 在运行中
- 用 `127.0.0.1:5150` 在服务器本机确认能打开
- 防火墙可能阻止外来连接 → 控制面板 → Windows Defender 防火墙 → 允许应用通过防火墙 → 添加 Python

**速度慢？**
- Tailscale 默认优先直连，不经过中继
- 如果两个办公区都是运营商 NAT，可能自动走 DERP 中继（延迟 < 50ms）

**需要卸载吗？**
- Tailscale 不影响任何网络配置
- 不需要的话放着就行，不占资源（内存 < 30MB）


## 五、额外：开机自启

服务器电脑建议设置 Tailscale 开机自启：

1. 托盘右键 → Settings
2. 勾选 "Run unattended"（允许未登录时运行）
3. 同时把 `启动.bat` 加入 Windows 开机启动：
   - Win+R → `shell:startup`
   - 右键 → 新建 → 快捷方式
   - 浏览 → 选 `D:\YIONpro\几何星球AUTO\启动.bat`
