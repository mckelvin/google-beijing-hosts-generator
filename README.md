# Google(Beijing) hosts generator

这个工具做了三件事：

1. 用ping暴力扫描Google北京IP段的存活主机
2. 遍历检测所有存活主机443端口SSL证书的subject common name(CN) 得到`IP-域名`的映射
3. 对`google_domains.txt`中每个每个域名进行解析

其中步骤1和步骤2的结果默认会被缓存在`db.shelve`中

## 安装依赖
   
    pip install -r requirements.txt

## 使用

    cd src
    python main.py # 可选 -f 会强制执行步骤1和步骤2
    # 运行完毕后 main.py 同目录会生成hosts文件。其中有些域名可能不能被正常解析，这时你可能要手动打个patch
    patch hosts postfix.patch
