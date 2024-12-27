from locust import HttpUser, task, between

# 要测试的接口 URL
interface_url = "http://location.leigod.com/geoip2/index.php"

class InterfaceUser(HttpUser):
    wait_time = between(0, 1)

    @task
    def test_interface(self):
        response = self.client.get(interface_url)
        # 这里可以根据需要对响应进行更多处理，比如检查状态码、内容等

def print_results(environment):
    if environment.stats.total.fail_ratio > 0.01:
        print(f"Test failed due to failure ratio > 1%: {environment.stats.total.fail_ratio}")
    else:
        print(f"Test passed with success ratio: {1 - environment.stats.total.fail_ratio}")
        print(f"Total requests: {environment.stats.total.requests}")
        print(f"Total response time: {environment.stats.total.response_time}")
        print(f"Average response time: {environment.stats.total.response_time / environment.stats.total.requests}")
        print(f"Requests per second: {environment.stats.total.requests / environment.stats.total.duration}")