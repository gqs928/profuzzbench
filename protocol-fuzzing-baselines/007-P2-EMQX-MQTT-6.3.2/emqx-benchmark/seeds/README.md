# 种子语料

镜像构建期间会由 `prepare_seeds.py` 以可复现方式生成种子输入。语料包括 MQTT 3.1.1 和 MQTT 5.0 会话，以及错误帧格式用例。

生成的二进制输入位于容器内的 `/home/ubuntu/experiments/in-mqtt`。
