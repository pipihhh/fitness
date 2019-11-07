class InsertMap(object):
    user = """
        INSERT INTO ezgym.user(account,password,permission,number) VALUES(%s,%s,%s,%s)
        """
    user_info = """
        INSERT INTO ezgym.user_info(
        user_id,phone,email,gender,age,nick_name,description,
        create_time
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

    course = """
        INSERT INTO ezgym.course(type, name, create_time, level, burning) VALUES (%s,%s,%s,%s,%s)
    """

    action = """
        INSERT INTO ezgym.course_action(course_id, content, picture, sequence) VALUES (%s,%s,%s,%s)
    """


class SelectMap(object):
    user_by_number = """
        SELECT id FROM ezgym.user WHERE number = %s
    """
    user_info_by_user_id = """
        SELECT u.id,u.account,u.permission,
        ui.phone,ui.email,ui.gender,ui.avatar,
        ui.description
        FROM ezgym.user u INNER JOIN ezgym.user_info ui
        ON u.id = ui.user_id WHERE u.id = %s AND u.delete_flag = 0 AND ui.delete_flag = 0
    """
    user_by_account = """
        SELECT id, account FROM ezgym.user WHERE account = %s AND delete_flag = 0
    """
    user_info_with_login = """
        SELECT u.id,u.account,u.permission,
        ui.phone,ui.email,ui.gender,ui.avatar,
        ui.description,u.password
        FROM ezgym.user u INNER JOIN ezgym.user_info ui
        ON u.id = ui.user_id WHERE u.account = %s AND u.delete_flag = 0 AND ui.delete_flag = 0 AND u.password = %s
    """

    user_valid = """
        SELECT id,account,password FROM ezgym.user WHERE account = %s
    """

    user_valid_by_id = """
        SELECT id,password,permission FROM ezgym.user WHERE id = %s AND delete_flag = 0
    """

    # 查询所有的用户 带分页
    user_list_by_offset = """
        SELECT u.id,u.permission,u.account,
        ui.nick_name,ui.age,ui.avatar,ui.gender,ui.email,ui.phone,ui.description,
        ui.create_time
        FROM ezgym.user u INNER JOIN ezgym.user_info ui ON u.id=ui.user_id
        WHERE u.delete_flag=0 AND ui.delete_flag=0 AND u.id>%s ORDER BY u.id LIMIT %s
    """

    user_count = """
        SELECT COUNT(1) FROM ezgym.user WHERE delete_flag=0;
    """

    course_by_create = """
        SELECT id, type, name, create_time, level, burning FROM ezgym.course WHERE name = %s
    """

    course_by_id = """
        SELECT id,name,type,level,burning,create_time FROM ezgym.course WHERE id = %s AND delete_flag = 0
    """


class DeleteMap(object):
    user_by_id = """
        UPDATE ezgym.user SET delete_flag = 1 WHERE id = %s
    """
    user_info_by_user_id = """
        UPDATE ezgym.user_info SET delete_flag = 1 WHERE user_id = %s
    """


class UpdateMap(object):
    update_avatar_by_user_id = """
        UPDATE ezgym.user_info SET avatar = %s WHERE user_id = %s
    """

    update_user_info_by_user_id = """
        UPDATE ezgym.user_info SET phone=%s,email=%s,gender=%s,avatar=%s,age=%s,nick_name=%s,description=%s
        WHERE user_id=%s
    """

    update_user_by_id = """
        UPDATE ezgym.user SET account = %s, password = %s WHERE id = %s AND delete_flag = 0
    """

    update_password_by_id = """
        UPDATE ezgym.user SET password = %s WHERE id = %s AND delete_flag = 0
    """

    update_description_by_id = """
        UPDATE ezgym.user_info SET description = %s WHERE user_id = %s
    """