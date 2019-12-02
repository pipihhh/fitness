import uuid
import datetime
import threading
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header
from utils.generic_import import *
from general.password_handler import md5


class Email(Resource):
    """
    这是一个 通过邮箱找回密码的接口 如果A申请了找回密码 但是 后台服务关闭了 那么此次找回会失败
    此接口POST方法 需要传想要找回密码的用户的邮箱
    """
    EMAIL_MAP = {}
    EMAIL_CONTENT = ""
    SMTP = None

    def __init__(self):
        self.SMTP = SMTP_SSL(current_app.config["EMAIL_HOST_SERVER"])
        if current_app.config["DEBUG"]:
            self.SMTP.set_debuglevel(1)
        import os
        with open(os.path.join(os.getcwd(), "conf", "email_template.html"), "r") as f:
            self.EMAIL_CONTENT = f.read()
        self.SMTP.ehlo(current_app.config["EMAIL_HOST_SERVER"])
        self.SMTP.login(current_app.config["EMAIL_SENDER"], current_app.config["EMAIL_SENDER_CODE"])

    def put(self):
        response = Response()
        kwargs = GeneralObject()
        resp = post(EmailValid, request.json, kwargs)
        if resp:
            return jsonify(resp.dict_data)
        try:
            password = md5(kwargs.password)
            ret = execute_sql(UpdateMap.update_user_by_email, (password, g.user.id))
            if ret == 0:
                raise InvalidArgumentException("修改失败!请勿使用原密码")
            self.EMAIL_MAP.pop(kwargs.email)
        except Exception as e:
            init_error_message(response, message=str(e))
        return jsonify(response.dict_data)

    def post(self):
        response = Response()
        try:
            valid = EmailValid(request.json)
            errs = valid.valid_data()
            if errs:
                response.data = errs
                response.errno = len(errs)
                response.code = FORMAT_ERROR
                return jsonify(response.dict_data)
            email = valid.clean_data
            uid = str(uuid.uuid4())
            now = datetime.datetime.now()
            self.EMAIL_MAP[email["email"]] = {
                "uid": uid, "create_time": now
            }
            url = f"{current_app.config['CALLBACK_URL']}?uid={uid}&_sid={uuid.uuid4()}&email={email['email']}"
            threading.Thread(target=self._send_email, args=(url, email["email"], current_app.config)).start()
            response.data = {
                "msg": "邮件已发送"
            }
        except UserAlreadyExistException as e:
            response.code = SERVER_ERROR
            response.errno = 1
            response.data = str(e)
        except Exception as e:
            init_error_message(response, message=str(e))
        return jsonify(response.dict_data)

    def __del__(self):
        self.SMTP.quit()

    def _send_email(self, url, receiver, config):
        charset = config["DB_CHARSET"]
        sender = config["EMAIL_SENDER"]
        message = MIMEText(self.EMAIL_CONTENT.format(url), "html", charset)
        message["Subject"] = Header(config["EMAIL_TITLE"], charset)
        message["From"] = sender
        message["To"] = Header(config["RECEIVER_NICK"], charset)
        self.SMTP.sendmail(sender, [receiver, ], message.as_string())


class EmailValid(BaseValid):
    def valid(self):
        if hasattr(self, "email"):
            if request.method == "PUT":
                email = getattr(self, "email")
                uid = getattr(self, "uid")
                if email in Email.EMAIL_MAP:
                    if Email.EMAIL_MAP[email]["uid"] == uid:
                        return
                    raise InvalidArgumentException("错误的uid")
            return
        raise InvalidArgumentException("缺少email字段")

    def email_valid(self, email):
        user = fetchone_dict(SelectMap.user_by_email, (email,), GeneralObject)
        if user is None:
            raise InvalidArgumentException("用户不存在!")
        g.user = user
        now = datetime.datetime.now()
        delta = datetime.timedelta(seconds=60)
        if email in Email.EMAIL_MAP and now - Email.EMAIL_MAP[email]["create_time"] <= delta:
            raise UserAlreadyExistException("邮件已发送")
