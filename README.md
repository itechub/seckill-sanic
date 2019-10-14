# Sanic-Seckill

An Simple Seckill Scenario implemented by Sanic web framework, using microservices style.  
This project simulate an simple seckill scenario, which is consist of three microservices as follow:

* Prodct Service
	* any user can query products and product details
	* any user can add/delete/edit product instance
* Activity Service
	* any user can query activities and activity details
	* any user can add/delete/edit activity instance
	* any user can participant seckill activity to place an order with unique user id.
* Order Service
	* user can query their orders, identify bu unique user id
	* user can view/delete order details


Read this in other languages:  [English][English], [简体中文][简体中文]

[English]: https://github.com/itechub/seckill-sanic/blob/master/README.md
[简体中文]: https://github.com/itechub/seckill-sanic/blob/master/README.zh-cn.md

## Original Requirements Description
	Write an web api service to simulate users' participation of an seckill activity:
	* Provide a web API, based on HTTP or TCP, which users can place their order for specific activity
	* User can send request over once to the same activity, and the server side should ensure that only one order is being placed when conditions are met.(only when there are products left)
	* The orders info should be persistent even when the service or machine is being restarted.
	* Each Activity only related to one product, user can only place order when activity's product inventory > 0.
	* The final products sums up within orders should be equivalent to inventory of the products.
	* The service should be able to handle large amount concurrent requests from multiple users.(etc. 100 TPS)

## Features
* **Using [Sanic][sanic] , Async Python 3.6+ web server/framework | Build fast. Run fast**
* **Using [aiomysql][aiomysql] as database driver, to execute sql statement asynchronously**
* **Using [aiohttp][aiohttp] as client to issue async http requst, interacting with other microservices.**
* **Using [peewee][peewee] as ORM，Only for modeling and data model migrations**
* **Using [sanic-opentracing][sanic-opentracing] as distributed tracing system implementation**
* **Using [sanic-openapi][sanic-openapi] to auto generate Swagger API documentation**

[sanic]: https://github.com/huge-success/sanic
[aiomysql]: https://github.com/aio-libs/aiomysql
[aiohttp]:https://github.com/aio-libs/aiohttp
[peewee]: https://github.com/coleifer/peewee
[sanic-opentracing]: https://github.com/shady-robot/sanic-opentracing
[sanic-openapi]: https://github.com/huge-success/sanic-openapi

## Screenshot
### Swagger API
![Swagger](https://github.com/itechub/seckill-sanic/raw/master/assets/images/swagger_sanic.jpg)

### Jaeger Server
![Jaeger](https://github.com/itechub/seckill-sanic/raw/master/assets/images/jaeger_sanic.jpg)

## Environment
### Docker-Compose Environment
#### Configure environment variables via `.env`
Create your local `.env` file, you can use the `.env_template` as a starting point.

```
DOCKER_DIR=~/you/project/patch/sanic_seckill/seckill/deployment
MYSQL_ROOT_PASSWORD=sanicroot
```

#### Start all services 
Build and Start all services with the following command using docker-compose. You can adjust the port mapping or other setting by editing the `docker-compose.yml` file.
```
docker-compose build 
docker-compose up 
```

#### Access services 
By default, docker-compose will bind services port to local host machine. Change any port mapping as you like by editing `docker-compose.yml` file.

* Consul UI:  `http://localhost:8501`
* Jaeger UI:  `http://localhost:8502`
* Product Service:  `http://localhost:8503`
* Activity Service:  `http://localhost:8504`
* Order Service:  `http://localhost:8505`

If everything works as expected, you can see all three microservices are registered with healthy check status in `consul` web GUI.

By default, `TRACE_ALL` is set to true within the `activity service`, which is configured in `docker-compose.yml`, so when you make request to `activity service`, you can view all request trace in jaeger web GUI.

### Local environment setup
#### docker volume 

#### Python virtualenv

## Technical implementation
### Server
#### Before server start
* Create DB Connection Pool
* Create Client connection session，to interact with other services
* Create `jaeger.tracer ` to implement distributed tracing over requests

#### Middleware
* Implement request middleware to add specific http headers, handle CORS request
* Add an envelop to response, uniform all response data format.

#### Exceptions
Intercept with exception, and response with uniform format. 

#### Service Registration
Create ServiceWatcher Task, for service discovery and service healthy status check, all services are maintained to `app.services` list.

### Data Model
> Using peewee as ORM backend, only for data model design and migration, using `aiomysql` for async sql operation.

* All DB connection configurations are configured by environment variables
* If you are using `docker-compose`, you don't have to create db table manually
* Otherwise you need to run `python migrations.py` to migrate db table.

### Database Operation
Using `aiomysql` as database connector, all sql related operation are capsulated by `DBConnection`, to execute raw sql asynchronously,

* acquire() return a non-transaction sql connection. Used for query which is optimized for efficiency.
* tansaction() as transaction function, all delete/insert related sql should use transaction when needed.
* If `trace` is set to true, all db operation will being traced.

### HTTP Async Request Client
Using `client` within `aiohttp` pacage, capsulating to provide common utilities for accessing other microservices asyncronously.

### Logging
Using python log module, `logging,yml` as configuration file, JsonFormatter will transform logs into json format.

### Distributed Tracing System
* OpenTracing is built around by Dapper, Zipkin, which bring us a standard for distributed tracing system.
* Opentracing will trace every requests within your service, and every related services, which plays an critical part for analysis of microservice performance.
* Implementing opentracing standard, and use jaeger as tracer.
* Tracing behaviors(DB, Client) can be configured by environment variable.

### Exceptions
Using `app.error_handler = CustomHander()` to to hande exceptions.

* code: status code, 0 for succeed, and other for exceptions. 
* message: error message
* status_code: http standard status code

