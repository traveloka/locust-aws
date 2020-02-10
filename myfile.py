from locust import HttpLocust, TaskSet

def login(l):
    print('login')
    #l.client.post("/login", {"username":"ellen_key", "password":"education"})

def logout(l):
    #l.client.post("/logout", {"username":"ellen_key", "password":"education"})
    print('logout')

def get(l):
    l.client.get("/get")

class UserBehavior(TaskSet):
    tasks = {get: 2}

    def on_start(self):
        login(self)

    def on_stop(self):
        logout(self)

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
