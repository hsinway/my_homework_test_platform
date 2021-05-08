import os

from flask import Flask, request
from flask_restful import Api, Resource, abort
from flask_sqlalchemy import SQLAlchemy
from jenkinsapi.jenkins import Jenkins

app = Flask(__name__)
api = Api(app)
# 用来给app做全局配置,存数据的地方
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:user@172.21.115.119/testcase_db?charset=utf8mb4'
db = SQLAlchemy(app)


class TestCaseTable(db.Model):
    """
    测试用例存储表
    """
    name = db.Column(db.String(80), primary_key=True)  # 数据名
    description = db.Column(db.String(80), unique=False, nullable=True)  # 描述
    file_name = db.Column(db.String(80), unique=False, nullable=False)  # 传入测试用例文件名
    content = db.Column(db.String(300), unique=False, nullable=False)  # 测试用例内容
    report = db.relationship("AllureReportTable", backref="test_case_table",
                             lazy=True)

    # 通过report建立test_case_table和allure_report_table的关系,当test_case_table.report.dir时候可以直接使用allure_report_table的dir字段

    def __repr__(self):
        return '<TestCase %r>' % self.name


class AllureReportTable(db.Model):
    """
    测试报告存储表
    """
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(80), unique=False, nullable=True)  # 描述
    dir = db.Column(db.String(300), unique=False, nullable=False)  # 报告路径
    testcase_name = db.Column(db.String(80), db.ForeignKey("test_case_table.name"),
                              nullable=False)  # 外键,指向test_case_table表的name字段

    def __repr__(self):
        return '<TestCase %r>' % self.name


# 测试用例存储
class TestCaseStore(Resource):

    def post(self):
        """
        存储测试用例
        切换到../flask_api_2/test_case下
        执行 curl -F "file=@test_case_orig.py" -F "name=homework" http://172.21.112.1:5000/testcase_store 传入文件和表单信息至数据库
        :return:
        """
        if "file" in request.files and "name" in request.form:
            f = request.files["file"]  # 通过curl命令传入文件后拿到文件流
            name = request.form["name"]
            file_name = f.filename
            content = f.read()  # 将文件内容转成字节流
            testcase = TestCaseTable(name=name, file_name=file_name, content=content)
            db.session.add(testcase)
            db.session.commit()
            return "Upload test case successfully!"
        abort(404)  # 返回不同的状态码,默认的错误页


# 监听路由地址172.21.112.1:5000/testcase_store
api.add_resource(TestCaseStore, '/testcase_store')


@app.route("/get_testcase", methods=["get"])
def get_testcase():
    """
    获取测试用例
    例如执行 curl -o "test_case_from_db.py" http://172.21.112.1:5000/get_testcase 将返回数据写入到test_case_from_db.py文件中
    :return:
    """
    # 检查url中是否指明了name
    if "name" in request.args:
        # 通过name,指定要运行的测试用例,并取出name值
        name = request.args["name"]
        # 通过name,查询出数据库中的数据
        testcase = TestCaseTable.query.filter_by(name=name).first()
        print("Download test case successfully!")
        return testcase.content  # 返回结果中的content字段内容
    abort(404)


@app.route("/run_testcase", methods=["get"])
def run_testcase():
    """
    调度jenkins运行测试用例
    例如执行 curl http://172.21.112.1:5000/run_testcase?name=homework 触发jenkinsapi操作项目 backend_platform_training构建运行
    也可以直接在浏览器中输入http://172.21.112.1:5000/run_testcase?name=homework来触发
    :return:
    """
    if "name" in request.args:
        name = request.args["name"]
        testcase = TestCaseTable.query.filter_by(name=name).first()  # 从数据库提取测试用例数据
        file_name = testcase.file_name
        J = Jenkins("http://127.0.0.1:8080", username="admin",
                    password="1104920790407542355104b4ec79b40325")  # 通过token和jenkins建立连接
        # print(J.keys())
        J["backend_platform_training"].invoke(
            build_params={"name": name, "file_name": file_name})  # 通过jenkinsapi调用项目进行构建
        return "Trigger test case running in jenkins successfully!"
    abort(404)


@app.route("/upload_allurereport", methods=["post"])
def upload_allurereport():
    """
    上传allure报告
    :return:
    """
    if "file" in request.files and "name" in request.form:
        folder = r"C:\Users\hsinway\Desktop\tmp_file"  # 这里存放目录应当选取flask api服务所在机器的路径,或者flask指定的路径,而不是jenkins节点的路径
        f = request.files["file"]
        name = request.form["name"]
        file_name = f.filename
        report_dir = os.path.join(folder, file_name)  # 拼接起指定的报告存放完成路径
        f.save(report_dir)  # 保存报告
        report = AllureReportTable(dir=report_dir, testcase_name=name)  # 将报告保存的信息存储至数据库
        db.session.add(report)
        db.session.commit()
        return "Upload test report successfully!"


if __name__ == '__main__':
    # db.drop_all() # 删除所有表
    # db.create_all()  # 创建新表
    app.run(host="172.21.112.1", debug=True)

"""
使用过程:
STEP1
切换到原始测试用例存放路径下执行curl -F "file=@test_case_orig.py" -F "name=homework" http://172.21.112.1:5000/testcase_store
上传测试用例到数据库
STEP2
执行 curl http://172.21.112.1:5000/run_testcase?name=homework 通过jenkinsapi触发项目 backend_platform_training运行
jenkins将下载测试用例,执行测试用例并生成allure报告,然后打包报告并上传到指定文件夹,上传信息存储至数据库

Jenkins项目backend_platform_training执行的shell命令:
# 使用当前环境下的命令,否则会出现pytest找不到的情况
. ~/.profile
# 调用flask的api来导出测试用例到节点的workspace
curl -o $file_name http://172.21.112.1:5000/get_testcase?name=$name
# 展示测试用例内容
cat $file_name
# 执行测试用例并生成allure报告
pytest -sv $file_name --clean-alluredir --alluredir $name
# 使用jar打包测试报告,--help查看参数解释
jar -cfM0 $name.zip $name
# 调用flask的api将打包后的报告存储并将存储信息上传到数据库
curl -F "file=@$name.zip" -F "name=$name" http://172.21.112.1:5000/upload_allurereport
"""