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

    challenge = """
        INSERT INTO ezgym.challenge(picture,content,start_time,end_time,create_time,pageviews,number) 
        VALUES(%s,%s,%s,%s,%s,%s,%s)
    """

    blog = """
        INSERT INTO ezgym.blog(user_id, content, title, picture, create_time) VALUES (%s,%s,%s,%s,%s)
    """

    upper = """
        INSERT INTO ezgym.upper_log(blog_id, user_id, create_time) VALUES (%s,%s,%s)
    """

    comment = """
        INSERT INTO ezgym.comment(content, create_time, blog_id, user_id, nick_name) VALUES (%s,%s,%s,%s,%s)
    """


class SelectMap(object):
    user_by_number = """
        SELECT id FROM ezgym.user WHERE number = %s
    """
    user_info_by_user_id = """
        SELECT u.id,u.account,u.permission,
        ui.phone,ui.email,ui.gender,ui.avatar,
        ui.description,ui.nick_name,ui.create_time
        FROM ezgym.user u INNER JOIN ezgym.user_info ui
        ON u.id = ui.user_id WHERE u.id = %s AND u.delete_flag = 0 AND ui.delete_flag = 0
    """
    user_by_account = """
        SELECT id, account FROM ezgym.user WHERE account = %s AND delete_flag = 0
    """
    user_info_with_login = """
        SELECT u.id,u.account,u.permission,
        ui.phone,ui.email,ui.gender,ui.avatar,
        ui.description,u.password,ui.create_time,ui.nick_name
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

    action_by_course_id = """
        SELECT id,course_id,sequence FROM ezgym.course_action WHERE course_id = %s
    """

    course_list_by_page = """
        SELECT id,type,name,create_time,level,burning FROM ezgym.course
        WHERE id > %s AND delete_flag = 0 ORDER BY id LIMIT %s
    """

    challenge_by_number = """
        SELECT id,picture,content,start_time,end_time,create_time,pageviews FROM ezgym.challenge WHERE number=%s AND delete_flag=0
    """

    challenge_by_id = """
        SELECT id,picture,content,start_time,end_time,create_time,pageviews FROM ezgym.challenge WHERE id=%s AND delete_flag=0
    """

    blog_list_by_id = """
        SELECT id, user_id, title, picture, create_time, `upper` FROM ezgym.blog WHERE id>%s AND delete_flag=0 ORDER BY id LIMIT %s
    """

    blog_by_id = """
        SELECT id, user_id, content, title, picture, create_time, `upper` FROM ezgym.blog WHERE id=%s AND delete_flag=0
    """

    action_list_by_course_id = """
        SELECT ca.id as id,ca.course_id as course_id,ca.content as content,ca.picture as picture,ca.sequence as sequence 
        FROM ezgym.course_action ca INNER JOIN ezgym.course c ON c.id=ca.course_id
        WHERE c.id=%s AND c.delete_flag=0 ORDER BY sequence
    """

    upper_by_user_and_blog = """
        SELECT id, blog_id, user_id, create_time FROM ezgym.upper_log WHERE delete_flag=0 AND blog_id=%s AND user_id=%s
    """

    upper_without_delete_flag = """
        SELECT id, blog_id, user_id, create_time FROM ezgym.upper_log WHERE blog_id=%s AND user_id=%s
    """

    challenge_list_by_id = """
        SELECT id, picture, content, start_time, end_time, create_time, pageviews 
        FROM ezgym.challenge WHERE id>%s AND delete_flag=0 ORDER BY id 
        LIMIT %s
    """


class DeleteMap(object):
    user_by_id = """
        UPDATE ezgym.user SET delete_flag = 1 WHERE id = %s
    """
    user_info_by_user_id = """
        UPDATE ezgym.user_info SET delete_flag = 1 WHERE user_id = %s
    """

    course_by_id = """
        UPDATE ezgym.course SET delete_flag=1 WHERE id=%s AND delete_flag=0
    """

    blog_by_id = """
        UPDATE ezgym.blog SET delete_flag=1 WHERE id=%s
    """

    upper_by_id = """
        UPDATE ezgym.upper_log SET delete_flag=1 WHERE blog_id=%s AND user_id=%s AND delete_flag=0
    """

    comment_by_id = """
        UPDATE ezgym.comment SET delete_flag=1 WHERE delete_flag=0 AND id=%s
    """

    reply_by_comment_id = """
        UPDATE ezgym.reply SET delete_flag=1 WHERE comment_id=%s AND delete_flag=0
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

    update_course_by_id = """
        UPDATE ezgym.course SET name=%s,type=%s,level=%s,burning=%s WHERE id=%s AND delete_flag=0
    """

    update_challenge_pageviews = """
        UPDATE ezgym.challenge SET pageviews=pageviews+1 WHERE id=%s AND delete_flag=0
    """

    update_challenge_by_id = """
        UPDATE ezgym.challenge SET picture=%s,content=%s,start_time=%s,end_time=%s WHERE id=%s AND delete_flag=0    
    """

    update_upper_by_user_and_blog = """
        UPDATE ezgym.upper_log SET delete_flag=0 WHERE blog_id=%s AND user_id=%s
    """

    update_blog_upper_by_id = """
        UPDATE ezgym.blog SET upper=upper+1 WHERE delete_flag=0 AND id=%s
    """

    blog_upper_dev = """
        UPDATE ezgym.blog SET upper=upper-1 WHERE delete_flag=0 AND id=%s
    """
