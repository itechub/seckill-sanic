# Sanic-Seckill

基于 sanic 实现秒杀场景需求，采用微服务基础架构实现。

## 需求描述
	编写一个 web 服务实现大量用户抢购某个商品的功能。要求：
	1. 提供一个 web API，可以基于 HTTP 或 TCP，输入为一个用户 ID，输出该用户是否抢到商品；
	2. 最终被抢到的商品的数量要等于库存数量；
	3. 每个用户会连续发送两次抢购请求（无论第一次抢没抢到），但是系统要保证一个用户最多只能抢到一个商品，不能多抢，最终抢到商品的用户数应该等于商品的库存数；
	4. 用户 ID 数至少是商品库存数的 100 倍；
	5. 抢购请求的吞吐量要超过关系式数据库处理能力至少一倍；
	6. 用户是否抢到商品的结果要持久化到磁盘上，重启服务后仍能查询到结果；
	7. 提供 web API 的程序只在一台电脑上运行，不做集群和负载均衡。

## 特性
* **使用 [sanic][sanic] 异步框架实现接口, 简洁，轻量，高效**
* **使用 [aiomysql][aiomysql] 为数据库驱动，进行数据库连接，异步执行sql语句**
* **使用 [aiohttp][aiohttp] 做异步 http 请求，对其他微服务进行访问**
* **使用 [peewee][peewee] 为ORM，用于做模型设计**
* **使用 [sanic-opentracing][sanic-opentracing] 做分布式追踪系统**
* **使用 [sanic-openapi][sanic-openapi] 自动生成 Swagger API 文档**

[sanic]: https://github.com/huge-success/sanic
[aiomysql]: https://github.com/aio-libs/aiomysql
[aiohttp]:https://github.com/aio-libs/aiohttp
[peewee]: https://github.com/coleifer/peewee
[sanic-opentracing]: https://github.com/shady-robot/sanic-opentracing
[sanic-openapi]: https://github.com/huge-success/sanic-openapi

## 运行截图

### Swagger API
![Swagger](https://github.com/itechub/seckill-sanic/raw/master/assets/images/swagger_sanic.jpg)

### Jaeger Server
![Jaeger](https://github.com/itechub/seckill-sanic/raw/master/assets/images/jaeger_sanic.jpg)

## 运行环境
### docker 运行环境
```
docker-compose up -d
```

### 开发环境搭建
> 设置环境变量值 SANIC_CONFIG_MODULE

```
export SANIC_SETTINGS_MODULE=product.settings
export TRACE_ALL=True
```

## 相关技术实现
### Server
功能说明：

#### Before Server Start

* 创建 DB 连接池
* 创建 Client 连接
* 创建 jaeger.tracer 进行日志追踪

#### Middleware

* 处理跨域请求
* 对 response 进行封装，统一格式

#### Error Handler

对抛出的异常进行处理，返回统一格式

#### Task

创建 ServiceWatcher 任务，进行服务发现以及服务状态维护


### 数据模型

> ORM 使用 peewee, 用于模型设计和 migration, 数据操作使用 aiomysql

* 确保配置了相关服务的 DB 链接参数
* 运行命令 python migrations.py 进行模型创建


### 数据库操作 
使用 aiomysql为数据库驱动, 对数据库连接进行封装, 执行数据库操作。

* acquire() 函数为非事务, 对于只涉及到查询的使用非事务，可以提高查询效率
* tansaction() 函数为事务操作，对于增删改必须使用事务操作
* 如果 trace 为真，则注入 span，进行日志追踪


### HTTP 异步请求客户端

使用aiohttp中的client，对客户端进行了简单的封装，异步访问其他微服务。


### 日志处理
使用官方logging, 配置文件为logging.yml，JsonFormatter将日志转成json格式。


### 分布式追踪系统

* OpenTracing是以Dapper，Zipkin等分布式追踪系统为依据, 为分布式追踪建立了统一的标准。
* Opentracing跟踪每一个请求，记录请求所经过的每一个微服务，以链条的方式串联起来，对分析微服务的性能瓶颈至关重要。
* 使用opentracing框架，但是在输出时转换成 jaeger 格式。
* 通过环境变量决定是否对 DB、Client 进行追踪


### 异常处理

使用 app.error_handler = CustomHander() 对抛出的异常进行处理

* code: 错误码，无异常时为0，其余值都为异常
* message: 状态码信息
* error: 自定义错误信息
* status_code: http状态码，使用标准的http状态码


