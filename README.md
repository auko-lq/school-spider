# school-spider

爬取华南师范大学正方教务系统成绩

- 功能
  - 查询成绩
  - 平均**六分钟**的频率监听成绩（频率不敢设得太高，怕正方承受不住..）
  - 可以选择有新成绩出来时发送到**指定邮箱**（很可能会在垃圾箱，请在邮箱的**反垃圾设置**里将aukocharlie@qq.com设为白名单）
  - 程序默认会**尝试自动登录**，如果您想**换个账号登录**可以把生成的cookies或temp文件**删除后再开启程序**
- 异常处理
  - 检查是否存在**异常行为**（比如，高频率地访问），因为说到底只是个爬虫，不能突破正方服务器的限制
  - 尝试去**浏览器登录**看看（可能系统关闭了查询接口，也可能您没有完成教学质量评价，作者也无解）
  - 把程序**生成的文件删除**掉，重新开启
- 发邮件时用的SMTP授权码已去除，可按需换成自己的

<img src="https://github.com/aukocharlie/school-spider/tree/master/imgs\查询成绩.png" alt="查询成绩" style="zoom:80%;" />

<img src="https://github.com/aukocharlie/school-spider/tree/master/imgs\发送邮箱.png" alt="发送邮箱" style="zoom:80%;" />

<img src="https://github.com/aukocharlie/school-spider/tree/master/imgs\邮件内容.png" alt="邮件内容" style="zoom:80%;" />
