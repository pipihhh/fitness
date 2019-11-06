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
        ui.description
        FROM ezgym.user u INNER JOIN ezgym.user_info ui
        ON u.id = ui.user_id WHERE u.account = %s AND u.delete_flag = 0 AND ui.delete_flag = 0 AND u.password = %s
    """

    user_valid = """
        SELECT COUNT(1) FROM ezgym.user WHERE account = %s
    """

    user_valid_by_id = """
        SELECT id,password FROM ezgym.user WHERE id = %s AND delete_flag = 0
    """


class DeleteMap(object):
    user_by_id = """
        UPDATE ezgym.user SET delete_flag = 1 WHERE id = %s
    """
    user_info_by_user_id = """
        UPDATE ezgym.user_info SET delete_flag = 1 WHERE id = %s
    """


class UpdateMap(object):
    update_avatar_by_user_id = """
        UPDATE ezgym.user_info SET avatar = ? WHERE user_id = ?
    """

    update_user_info_by_user_id = """
        UPDATE ezgym.user_info SET phone=?,email=?,gender=?,avatar=?,age=?,nick_name=?,description=?
        WHERE user_id=?
    """

    update_user_by_id = """
        UPDATE ezgym.user SET account = ?, password = ? WHERE id = ? AND delete_flag = 0
    """

    update_password_by_id = """
        UPDATE ezgym.user SET password = ? WHERE id = ? AND delete_flag = 0
    """
