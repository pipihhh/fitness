import random
from io import BytesIO
from flask import current_app, Response, session
from flask_restful import Resource
from utils.throttle import throttle
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class AuthCode(Resource):

    @throttle(5, 1)
    def get(self):
        buffer, code = _generate_code_picture()
        key = current_app.config["AUTH_CODE_SESSION_KEY"]
        session[key] = code
        response = Response(buffer, mimetype="image/png")
        response.headers.add("Pragma", "no-cache")
        response.headers.add("Cache-Control", "no-cache")
        return response


def _generate_code_text():
    length = current_app.config["AUTH_CODE_LENGTH"]
    code = ""
    for i in range(length):
        current = random.randrange(0, length)
        if i == current:
            tep = str(chr(random.randint(65, 97)))
            if random.randint(0, 1) == 0:
                tep = tep.upper()
        else:
            tep = str(random.randint(0, 9))
        code += tep
    return code


def _generate_code_picture():
    """
    生成二维码图片的函数 借助PIL库来实现 都是可配置的
    :return: 返回图片的二进制流和验证码
    """
    width = current_app.config["AUTH_CODE_WIDTH"]
    height = current_app.config["AUTH_CODE_HEIGHT"]
    background_color = current_app.config["AUTH_CODE_BG_COLOR"]
    number = current_app.config["AUTH_CODE_LENGTH"]
    image = Image.new("RGBA", (width, height), background_color)
    font = ImageFont.truetype(current_app.config["AUTH_CODE_FONT"], current_app.config["AUTH_CODE_FONTSIZE"])
    draw = ImageDraw.Draw(image)
    code = _generate_code_text()
    for index, alpha in enumerate(code):
        font_width, font_height = font.getsize(alpha)
        draw.text(
            (index * ((width - font_width) / number), index * ((height - font_height) / number)),
            alpha, font=font, fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
    for _ in range(current_app.config["AUTH_CODE_LINES"]):
        begin = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        line_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.line((begin, end), fill=line_color)
    image = image.transform(
        (width + 20, height + 10), Image.AFFINE, (1, -0.3, 0, -0.1, 1, 0),
        Image.BILINEAR
    )
    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    f = BytesIO()
    image.save(f, 'png')
    return f.getvalue(), code
