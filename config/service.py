import logging
import consul
import consul.aio
import socket
import hashlib
import asyncio

from collections import defaultdict

logger = logging.getLogger("sanic")


class ServiceInfo(object):
    def __init__(
        self,
        service_name,
        service_id,
        service_address,
        service_port,
        node,
        address,
        service_tags=None,
    ):
        self.service_name = service_name
        self.service_id = service_id
        self.service_address = service_address
        self.service_port = service_port
        self.node = node
        self.address = address
        self.service_tags = service_tags

    def __eq__(self, value):
        return self.service_id == value.service_id

    def __ne__(self, value):
        return not self.__eq__(value)

    def __hash__(self):
        return hash(self.service_id or self.service_address or self.service_name)


class ServiceManager(object):
    def __init__(self, name=None, loop=None, host="127.0.0.1", port=8500, **kwargs):
        self.name = name
        self.service_id = name
        self.consul = consul.aio.Consul(host=host, port=port, loop=loop, **kwargs)

    def get_host_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    async def register_service(self, host=None, port=None):
        logger.info("register service ==> port: {}".format(port))
        if not port:
            return
        m = hashlib.md5()
        address = host or self.get_host_ip()
        logger.info("register service ==> host:{}, port:{}".format(address, port))
        url = "http://{}:{}/".format(address, port)
        m.update(url.encode("utf-8"))
        self.service_id = m.hexdigest()
        service = self.consul.agent.service
        check = consul.Check.http(url, "10s")
        res = await service.register(
            self.name,
            service_id=self.service_id,
            address=address,
            port=port,
            check=check,
        )
        logger.info(
            "register service: name:{}, service_id:{}, address:{}, port:{}, res:{}".format(
                self.name, self.service_id, address, port, res
            )
        )

    async def deregister(self):
        service = self.consul.agent.service
        await service.deregister(self.service_id)
        logger.info("deregister service: {}".format(self.service_id))

    async def discover_all_services(self):
        catalog = self.consul.catalog
        result = await catalog.services()
        return result

    async def discover_services(self, service_name):
        catalog = self.consul.catalog
        result = await catalog.service(service_name)
        # construct ServiceInfo object
        services = []
        if result:
            for service in result[1]:
                services.append(
                    ServiceInfo(
                        service_name=service["ServiceName"],
                        service_id=service["ServiceID"],
                        service_address=service["ServiceAddress"],
                        service_port=service["ServicePort"],
                        node=service["Node"],
                        address=service["Address"],
                        service_tags=service["ServiceTags"],
                    )
                )
        return services

    async def check_service(self, service_name):
        health = self.consul.health
        checks = await health.checks(service_name)
        res = {}
        # for check in checks[1:][0]:
        for check in checks[1]:
            res[check["ServiceID"]] = check
        return res


async def service_watcher(app, loop):
    """
    Service watcher to query consul api, and update related service list
    """
    service = ServiceManager(loop=loop, host=app.config["CONSUL_AGENT_HOST"])
    app.services = defaultdict(list)
    while True:
        services = await service.discover_all_services()
        for name in services[1].keys():
            if "consul" == name:
                continue
            result = await service.discover_services(name)
            # checks = await service.check_service(name)
            # filter all services
            service_ids = [item.service_id for item in app.services[name]]
            # Service health check
            checks = await service.check_service(name)

            # : Remove unhealthy service
            for index, value in enumerate(app.services[name]):
                if value.service_id not in checks:
                    del app.services[name][index]
                    continue
                status = checks[value.service_id]["Status"]
                if status != "passing":
                    del app.services[name][index]

            # : Add new healthy service
            for res in result:
                status = checks[res.service_id]["Status"]
                # Add new healthy service
                if res.service_id not in service_ids:
                    if status == "passing":
                        app.services[name].append(res)

        logger.info(f"Service list: {app.services}")
        await asyncio.sleep(20)
