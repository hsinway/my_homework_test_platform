from flask import Flask, escape, request, session
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)
# 用来给app做全局配置,存数据的地方
app.config["testcase"] = []


class TestCaseServer(Resource):

    def post(self):
        """
        存数据,每条testcase要有id,description,steps
        :return:
        """
        # linux下执行命令post一些含有id的数据
        # curl -v -X POST -H "Content-Type:application/json" -d '{"id":300, "steps":"run app", "description":"testcase 300"}' 172.21.112.1:5000/testcase
        # curl -v -X POST -H "Content-Type:application/json" -d '{"id":301, "steps":"run app", "description":"testcase 300"}' 172.21.112.1:5000/testcase
        # curl -v -X POST -H "Content-Type:application/json" -d '{"id":302, "steps":"run app", "description":"testcase 300"}' 172.21.112.1:5000/testcase
        if "id" not in request.json:  # 如果post数据中没有id则返回错误提示
            return {"result": "error", "errcode": "404", "errmessage": "need testcase id"}
        app.config["testcase"].append(request.json)
        return {"result": "ok", "errcode": "0"}

    def get(self):
        """
        读取数据
        :return:
        """
        # 当post方法传入数据后,
        # 浏览器输入不带参数url: http://172.21.112.1:5000/testcase可以返回所有保存的数据
        # 浏览器输入带参数url: http://172.21.112.1:5000/testcase?id=302.就可以直接返回对应的数据
        print(app.config["testcase"])
        if "id" in request.args:
            # 从用例库中找对应的用例
            for i in app.config["testcase"]:
                print(i["id"])
                # 返回用例
                # 这里request.args打印出来的url参数id的值实际上是str要再转成int
                if i["id"] == int(request.args["id"]):
                    return i
        else:
            return app.config["testcase"]


# 监听路由地址172.21.112.1:5000/testcase
api.add_resource(TestCaseServer, '/testcase')

# 如果设置host="0.0.0.0" 则是监听局域网内所有请求
# 如果设置本机ip地址,外网访问时可能需要本机关闭防火墙
# 端口号默认5000
# 一旦源代码做过修改,本flask将自动重启服务,则之前post的数据都会清空
if __name__ == '__main__':
    app.run(host="172.21.112.1", debug=True)
