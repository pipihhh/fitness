/* =========================================================================
   ezgym API 数据 —— 按域分组的真实端点，源自 API_CONTRACT.md
   响应体固定 {errno, code, data}（errno=0 成功）
   auth: public(公开) | soft(软登录) | login(需登录) | admin(管理员)
   供 api.js 渲染；纯数据、无副作用。
   ========================================================================= */
window.EZGYM_API = {
  contract: {
    envelope: '{ "errno": 0, "code": 200, "data": { … } }',
    pagination: 'cursor(默认 0) + limit(默认 config.PAGE_OFFSET) → { items, next_cursor, count }',
    note: '跨域取数只经对方 service 门面；作者昵称/头像统一走 identity.get_users_public 批量取。'
  },

  domains: [
    /* ---------------------------------------------------------------- 01 */
    {
      id: 'identity', no: '01', name: 'identity', zh: '身份 · 认证 · 资料 · 主页聚合',
      desc: 'User + UserInfo。注册登录、验证码、找回/修改密码、用户管理，以及个人主页跨域聚合（blog/粉丝/关注/收藏计数经各域 service 取）。',
      endpoints: [
        {
          method: 'POST', path: '/api/auth/register', auth: 'public',
          desc: '注册新用户。permission 默认 NORMAL，前端传 ADMIN 提权将被忽略/拒绝。account/number 唯一冲突返回 409。',
          params: [
            { n: 'account', t: 'string', req: true, in: 'body', d: '登录账号，唯一' },
            { n: 'password', t: 'string', req: true, in: 'body', d: '明文密码，服务端 bcrypt 加盐哈希' },
            { n: 'nick_name', t: 'string', req: true, in: 'body', d: '昵称' },
            { n: 'phone', t: 'string', req: false, in: 'body', d: '手机号' },
            { n: 'gender', t: 'int', req: false, in: 'body', d: '性别' },
            { n: 'age', t: 'int', req: false, in: 'body', d: '年龄' },
            { n: 'email', t: 'string', req: false, in: 'body', d: '邮箱' },
            { n: 'avatar', t: 'string', req: false, in: 'body', d: '头像 URL' }
          ],
          reqBody: '{\n  "account": "coach_lee",\n  "password": "S3cure!pw",\n  "nick_name": "铁馆老李",\n  "gender": 1,\n  "email": "lee@ezgym.dev"\n}',
          res: '{\n  "errno": 0,\n  "code": 201,\n  "data": {\n    "id": 42,\n    "nick_name": "铁馆老李",\n    "avatar": "/media/images/default.jpg",\n    "permission": "NORMAL"\n  }\n}'
        },
        {
          method: 'POST', path: '/api/auth/login', auth: 'public',
          desc: '登录。先校验验证码（core.captcha，从 session 取，不匹配 400），再校验密码。密码走 body（修 CR #16，不再 GET query 入日志）。',
          cr: '修 CR #16 · 密码从 query 移入 body',
          params: [
            { n: 'account', t: 'string', req: true, in: 'body', d: '账号' },
            { n: 'password', t: 'string', req: true, in: 'body', d: '密码' },
            { n: 'captcha_code', t: 'string', req: true, in: 'body', d: '图形验证码文本' }
          ],
          reqBody: '{\n  "account": "coach_lee",\n  "password": "S3cure!pw",\n  "captcha_code": "8f3a"\n}',
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "token": "eyJhbGciOiJIUzI1NiIsIn…",\n    "user": {\n      "id": 42,\n      "nick_name": "铁馆老李",\n      "avatar": "/media/images/default.jpg",\n      "permission": "NORMAL"\n    }\n  }\n}'
        },
        {
          method: 'GET', path: '/api/auth/captcha', auth: 'public',
          desc: '返回 PNG 验证码图片（image/png），并把验证码文本写入 session。带限流。',
          params: [],
          reqBody: null,
          res: 'HTTP/1.1 200 OK\nContent-Type: image/png\n\n<binary PNG bytes>'
        },
        {
          method: 'POST', path: '/api/auth/password-reset', auth: 'public',
          desc: '发起找回密码。调 notification.service.send_password_reset_email(email)（惰性/异步）。始终返回成功，不暴露邮箱是否存在。',
          params: [{ n: 'email', t: 'string', req: true, in: 'body', d: '目标邮箱' }],
          reqBody: '{ "email": "lee@ezgym.dev" }',
          res: '{ "errno": 0, "code": 200, "data": { "sent": true } }'
        },
        {
          method: 'PUT', path: '/api/auth/password-reset', auth: 'public',
          desc: '通过邮件 token 重置密码。校验 token 后改密。',
          params: [
            { n: 'email', t: 'string', req: false, in: 'body', d: 'email 或 uid 二选一' },
            { n: 'uid', t: 'int', req: false, in: 'body', d: '用户 id' },
            { n: 'token', t: 'string', req: true, in: 'body', d: '邮件重置令牌' },
            { n: 'new_password', t: 'string', req: true, in: 'body', d: '新密码' }
          ],
          reqBody: '{\n  "email": "lee@ezgym.dev",\n  "token": "3b1c…",\n  "new_password": "N3wpass!"\n}',
          res: '{ "errno": 0, "code": 200, "data": { "reset": true } }'
        },
        {
          method: 'GET', path: '/api/users', auth: 'admin',
          desc: '游标分页用户列表。带限流。',
          params: [
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标，默认 0' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '每页条数' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "items": [\n      { "id": 42, "account": "coach_lee", "nick_name": "铁馆老李",\n        "avatar": "/media/images/default.jpg", "permission": "NORMAL",\n        "created_at": "2026-07-01 09:12:00" }\n    ],\n    "next_cursor": 41,\n    "count": 1\n  }\n}'
        },
        {
          method: 'PUT', path: '/api/users/me', auth: 'login',
          desc: '修改本人资料（nick_name/phone/gender/age/email/description/avatar 任意子集）。不改头像时回传原值不应报错（修 CR #15）。',
          cr: '修 CR #15 · 未改头像回传原值不报错',
          params: [
            { n: 'nick_name', t: 'string', req: false, in: 'body', d: '昵称' },
            { n: 'phone', t: 'string', req: false, in: 'body', d: '手机号' },
            { n: 'gender', t: 'int', req: false, in: 'body', d: '性别' },
            { n: 'age', t: 'int', req: false, in: 'body', d: '年龄' },
            { n: 'email', t: 'string', req: false, in: 'body', d: '邮箱' },
            { n: 'description', t: 'string', req: false, in: 'body', d: '个人简介' },
            { n: 'avatar', t: 'string', req: false, in: 'body', d: '头像 URL' }
          ],
          reqBody: '{ "nick_name": "老李教练", "age": 34 }',
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": { "id": 42, "nick_name": "老李教练", "age": 34 }\n}'
        },
        {
          method: 'PUT', path: '/api/users/me/password', auth: 'login',
          desc: '校验旧密码后改密。异常必须上抛（修 CR #6，禁止 finally return 吞异常）。',
          cr: '修 CR #6 · 禁止 finally return 吞异常',
          params: [
            { n: 'old_password', t: 'string', req: true, in: 'body', d: '旧密码' },
            { n: 'new_password', t: 'string', req: true, in: 'body', d: '新密码' }
          ],
          reqBody: '{ "old_password": "S3cure!pw", "new_password": "N3wpass!" }',
          res: '{ "errno": 0, "code": 200, "data": { "changed": true } }'
        },
        {
          method: 'DELETE', path: '/api/users/{id}', auth: 'admin',
          desc: '软删用户及其 user_info。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 42 } }'
        },
        {
          method: 'GET', path: '/api/users/{id}/profile', auth: 'soft',
          desc: '个人主页聚合：用户公开信息 + blog/粉丝/关注/收藏计数 + is_following（当前登录者是否已关注）。计数经各域 service 取。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '目标用户 id' }],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "user": { "id": 42, "nick_name": "老李教练", "avatar": "/media/images/default.jpg" },\n    "blog_count": 12,\n    "fans_count": 340,\n    "following_count": 58,\n    "collection_count": 7,\n    "is_following": true\n  }\n}'
        },
        {
          method: 'GET', path: '/api/users/{id}/blogs', auth: 'soft',
          desc: '用户发布的动态（分页子资源，数据经 content.service 取）。',
          params: [
            { n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' },
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '条数' }
          ],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "items": [ … ], "next_cursor": null, "count": 0 } }'
        },
        {
          method: 'GET', path: '/api/users/{id}/comments', auth: 'soft',
          desc: '用户发表的评论（分页，经 interaction.service 取）。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "items": [ … ], "next_cursor": null, "count": 0 } }'
        },
        {
          method: 'GET', path: '/api/users/{id}/collections', auth: 'soft',
          desc: '用户收藏的课程（分页，经 course.service 取）。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "items": [ … ], "next_cursor": null, "count": 0 } }'
        },
        {
          method: 'GET', path: '/api/users/{id}/followers', auth: 'soft',
          desc: '粉丝列表（分页，经 social.service 取），带对方公开信息。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "items": [ … ], "next_cursor": null, "count": 0 } }'
        },
        {
          method: 'GET', path: '/api/users/{id}/following', auth: 'soft',
          desc: '关注列表（分页，经 social.service 取），带对方公开信息。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "items": [ … ], "next_cursor": null, "count": 0 } }'
        },
        {
          method: 'GET', path: '/api/stats/registrations', auth: 'admin',
          desc: '按天注册量统计（跨度 ≤ 30 天）。原 /api/time。',
          params: [
            { n: 'start', t: 'string', req: true, in: 'query', d: '起始日 YYYY-MM-DD' },
            { n: 'end', t: 'string', req: true, in: 'query', d: '结束日 YYYY-MM-DD' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": [\n    { "date": "2026-07-20", "count": 12 },\n    { "date": "2026-07-21", "count": 9 }\n  ]\n}'
        }
      ]
    },

    /* ---------------------------------------------------------------- 02 */
    {
      id: 'course', no: '02', name: 'course', zh: '课程 · 动作 · 收藏',
      desc: 'Course + CourseAction + CourseCollection。课程与训练动作管理，用户收藏。列表每项带封面图（首个 action 图，无则默认图）。',
      endpoints: [
        {
          method: 'GET', path: '/api/courses', auth: 'soft',
          desc: '游标分页课程列表。每项带 picture；登录时带 is_collected + collection_id。',
          params: [
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '条数' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "items": [\n      { "id": 3, "name": "自重核心 30 天", "type": "core", "level": 2,\n        "burning": 240, "picture": "/media/images/core3.jpg",\n        "is_collected": true, "collection_id": 88 }\n    ],\n    "next_cursor": 2,\n    "count": 1\n  }\n}'
        },
        {
          method: 'GET', path: '/api/courses/{id}', auth: 'login',
          desc: '单个课程详情。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '课程 id' }],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": { "id": 3, "name": "自重核心 30 天", "type": "core", "level": 2, "burning": 240 }\n}'
        },
        {
          method: 'POST', path: '/api/courses', auth: 'admin',
          desc: '新建课程。name 唯一冲突 409。修 CR #4（原 InsertMap.course 占位符少一个）。',
          cr: '修 CR #4 · 补齐占位符',
          params: [
            { n: 'name', t: 'string', req: true, in: 'body', d: '课程名，唯一' },
            { n: 'type', t: 'string', req: true, in: 'body', d: '类型' },
            { n: 'level', t: 'int', req: true, in: 'body', d: '难度等级' },
            { n: 'burning', t: 'int', req: true, in: 'body', d: '预计消耗卡路里' }
          ],
          reqBody: '{ "name": "自重核心 30 天", "type": "core", "level": 2, "burning": 240 }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 3, "name": "自重核心 30 天" } }'
        },
        {
          method: 'PUT', path: '/api/courses/{id}', auth: 'admin',
          desc: '修改课程。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '课程 id' }],
          reqBody: '{ "level": 3, "burning": 300 }',
          res: '{ "errno": 0, "code": 200, "data": { "id": 3, "level": 3, "burning": 300 } }'
        },
        {
          method: 'DELETE', path: '/api/courses/{id}', auth: 'admin',
          desc: '软删课程。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '课程 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 3 } }'
        },
        {
          method: 'GET', path: '/api/courses/{id}/actions', auth: 'public',
          desc: '该课程所有动作（按 sequence 排序）+ 课程信息。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '课程 id' }],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "course": { "id": 3, "name": "自重核心 30 天" },\n    "actions": [\n      { "id": 11, "content": "平板支撑 45s", "picture": "/media/images/plank.jpg", "sequence": 1 }\n    ]\n  }\n}'
        },
        {
          method: 'POST', path: '/api/courses/{id}/actions', auth: 'admin',
          desc: '为课程新增动作。sequence 在同课程内不可重复 409。',
          params: [
            { n: 'id', t: 'int', req: true, in: 'path', d: '课程 id' },
            { n: 'content', t: 'string', req: true, in: 'body', d: '动作说明' },
            { n: 'picture', t: 'string', req: false, in: 'body', d: '动作示意图' },
            { n: 'sequence', t: 'int', req: true, in: 'body', d: '课内序号，唯一' }
          ],
          reqBody: '{ "content": "平板支撑 45s", "picture": "/media/images/plank.jpg", "sequence": 1 }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 11, "sequence": 1 } }'
        },
        {
          method: 'DELETE', path: '/api/actions/{id}', auth: 'admin',
          desc: '软删动作（原表硬删，现统一软删）。成功返回明确 data（修 CR #26）。',
          cr: '修 CR #26 · 硬删改软删 + 返回明确 data',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动作 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 11 } }'
        },
        {
          method: 'POST', path: '/api/collections', auth: 'login',
          desc: '收藏课程。已软删记录则恢复，否则新建。(user, course) 唯一。',
          params: [{ n: 'course_id', t: 'int', req: true, in: 'body', d: '课程 id' }],
          reqBody: '{ "course_id": 3 }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 88, "course_id": 3 } }'
        },
        {
          method: 'DELETE', path: '/api/collections/{id}', auth: 'login',
          desc: '软删收藏（只能删本人）。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '收藏 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 88 } }'
        }
      ]
    },

    /* ---------------------------------------------------------------- 03 */
    {
      id: 'challenge', no: '03', name: 'challenge', zh: '挑战活动',
      desc: 'Challenge（picture/content/start_time/end_time/pageviews/number）。独立无跨域依赖。浏览量自增改为独立原子端点，避免读改写竞态。',
      endpoints: [
        {
          method: 'GET', path: '/api/challenges', auth: 'public',
          desc: '游标分页。每项带从 content 截取的 title（前 config.TITLE_LENGTH 字）。',
          params: [
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '条数' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0,\n  "code": 200,\n  "data": {\n    "items": [\n      { "id": 5, "number": "CH20260720", "title": "夏日燃脂 21 天",\n        "picture": "/media/images/summer.jpg", "pageviews": 1820,\n        "start_time": "2026-07-01", "end_time": "2026-07-21" }\n    ],\n    "next_cursor": 4, "count": 1\n  }\n}'
        },
        {
          method: 'GET', path: '/api/challenges/{id}', auth: 'public',
          desc: '单个挑战。GET 不再自增 pageviews（修 CR #20）。',
          cr: '修 CR #20 · GET 不再自增浏览量',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '挑战 id' }],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": { "id": 5, "number": "CH20260720", "content": "<p>…</p>", "pageviews": 1820 }\n}'
        },
        {
          method: 'POST', path: '/api/challenges/{id}/views', auth: 'public',
          desc: '原子自增 pageviews（UPDATE pageviews = pageviews + 1，避免读改写竞态）。返回最新值。',
          cr: '修 CR #20 · 原子自增替代读改写',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '挑战 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "id": 5, "pageviews": 1821 } }'
        },
        {
          method: 'POST', path: '/api/challenges', auth: 'admin',
          desc: '新建挑战。number 自动生成唯一号。',
          params: [
            { n: 'picture', t: 'string', req: true, in: 'body', d: '封面图' },
            { n: 'content', t: 'string', req: true, in: 'body', d: '正文' },
            { n: 'start_time', t: 'string', req: true, in: 'body', d: '开始日 YYYY-MM-DD' },
            { n: 'end_time', t: 'string', req: true, in: 'body', d: '结束日 YYYY-MM-DD' }
          ],
          reqBody: '{\n  "picture": "/media/images/summer.jpg",\n  "content": "夏日燃脂 21 天，一起打卡！",\n  "start_time": "2026-07-01",\n  "end_time": "2026-07-21"\n}',
          res: '{ "errno": 0, "code": 201, "data": { "id": 5, "number": "CH20260720" } }'
        },
        {
          method: 'PUT', path: '/api/challenges/{id}', auth: 'admin',
          desc: '修改挑战。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '挑战 id' }],
          reqBody: '{ "end_time": "2026-07-28" }',
          res: '{ "errno": 0, "code": 200, "data": { "id": 5, "end_time": "2026-07-28" } }'
        },
        {
          method: 'DELETE', path: '/api/challenges/{id}', auth: 'admin',
          desc: '软删挑战。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '挑战 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 5 } }'
        }
      ]
    },

    /* ---------------------------------------------------------------- 04 */
    {
      id: 'content', no: '04', name: 'content', zh: '内容社区 · 动态 · 点赞',
      desc: 'Blog + Like。用户动态发布与点赞。列表可按 latest/following/user 过滤；正文用 bleach 白名单清洗 XSS。点赞计数与明细在同一事务内保持一致。',
      endpoints: [
        {
          method: 'GET', path: '/api/blogs', auth: 'soft',
          desc: '游标分页。scope: latest(默认) | following(关注的人，调 social.list_following_ids) | user(需 user_id)。每项带作者公开信息、comment_count、like_count，登录时 is_liked。',
          params: [
            { n: 'scope', t: 'enum', req: false, in: 'query', d: 'latest | following | user' },
            { n: 'user_id', t: 'int', req: false, in: 'query', d: 'scope=user 时必填' },
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '条数' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": {\n    "items": [\n      { "id": 77, "title": "今日 PR 更新", "content": "<p>硬拉 140kg…</p>",\n        "picture": "/media/images/dl.jpg", "like_count": 24, "comment_count": 6,\n        "is_liked": false,\n        "author": { "id": 42, "nick_name": "老李教练", "avatar": "/media/images/default.jpg" } }\n    ],\n    "next_cursor": 76, "count": 1\n  }\n}'
        },
        {
          method: 'GET', path: '/api/blogs/{id}', auth: 'public',
          desc: '单帖 + 作者信息 + comment_count + like_count。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动态 id' }],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": { "id": 77, "title": "今日 PR 更新", "like_count": 24, "comment_count": 6,\n    "author": { "id": 42, "nick_name": "老李教练" } }\n}'
        },
        {
          method: 'POST', path: '/api/blogs', auth: 'login',
          desc: '发布动态。content 用 bleach 白名单清洗 XSS（替代原 BeautifulSoup 只挡 script）。',
          cr: '修 CR · bleach 白名单清洗替代仅挡 script',
          params: [
            { n: 'title', t: 'string', req: true, in: 'body', d: '标题' },
            { n: 'content', t: 'string', req: true, in: 'body', d: '正文（服务端清洗）' },
            { n: 'picture', t: 'string', req: false, in: 'body', d: '配图 URL' }
          ],
          reqBody: '{ "title": "今日 PR 更新", "content": "硬拉 140kg 达成！", "picture": "/media/images/dl.jpg" }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 77, "title": "今日 PR 更新" } }'
        },
        {
          method: 'DELETE', path: '/api/blogs/{id}', auth: 'login',
          desc: '仅作者或 ADMIN 可删，软删。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动态 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 77 } }'
        },
        {
          method: 'POST', path: '/api/blogs/{id}/likes', auth: 'login',
          desc: '点赞。已软删 Like 则恢复，否则新建；同一事务内 like_count+1 与明细一致（修 CR #12）。重复点赞幂等。',
          cr: '修 CR #12 · 计数与明细单事务一致 + 幂等',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动态 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 201, "data": { "blog_id": 77, "is_liked": true, "like_count": 25 } }'
        },
        {
          method: 'DELETE', path: '/api/blogs/{id}/likes', auth: 'login',
          desc: '取消赞。同一事务内软删 Like + like_count-1（不小于 0）。',
          cr: '修 CR #12 · 单事务软删 + 计数不越界',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动态 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "blog_id": 77, "is_liked": false, "like_count": 24 } }'
        }
      ]
    },

    /* ---------------------------------------------------------------- 05 */
    {
      id: 'interaction', no: '05', name: 'interaction', zh: '评论 · 回复',
      desc: 'Comment + Reply。评论与楼中楼回复。无冗余昵称，展示昵称经 identity.get_users_public 实时取；发帖存在性经 content.blog_exists 校验。',
      endpoints: [
        {
          method: 'GET', path: '/api/blogs/{id}/comments', auth: 'public',
          desc: '该帖评论列表，每条评论内嵌其 reply 列表；评论与回复都带作者公开信息（批量取）。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '动态 id' }],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": [\n    { "id": 9, "content": "太强了！", "author": { "id": 7, "nick_name": "小王" },\n      "replies": [\n        { "id": 15, "content": "同感", "author": { "id": 42, "nick_name": "老李教练" }, "reply_id": null }\n      ] }\n  ]\n}'
        },
        {
          method: 'POST', path: '/api/comments', auth: 'login',
          desc: '发表评论。先 content.blog_exists 校验帖子存在，否则 NotFound。content HTML 转义。',
          params: [
            { n: 'blog_id', t: 'int', req: true, in: 'body', d: '动态 id' },
            { n: 'content', t: 'string', req: true, in: 'body', d: '评论内容' }
          ],
          reqBody: '{ "blog_id": 77, "content": "太强了！" }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 9, "blog_id": 77 } }'
        },
        {
          method: 'DELETE', path: '/api/comments/{id}', auth: 'login',
          desc: '仅作者或 ADMIN，软删评论 + 级联软删其 reply。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '评论 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 9 } }'
        },
        {
          method: 'POST', path: '/api/replies', auth: 'login',
          desc: '回复评论。reply_id 可选（回复某条 reply，楼中楼）。校验 comment 存在。',
          params: [
            { n: 'comment_id', t: 'int', req: true, in: 'body', d: '所属评论 id' },
            { n: 'content', t: 'string', req: true, in: 'body', d: '回复内容' },
            { n: 'reply_id', t: 'int', req: false, in: 'body', d: '被回复的 reply id' }
          ],
          reqBody: '{ "comment_id": 9, "content": "同感" }',
          res: '{ "errno": 0, "code": 201, "data": { "id": 15, "comment_id": 9 } }'
        },
        {
          method: 'DELETE', path: '/api/replies/{id}', auth: 'login',
          desc: '仅本人，软删。',
          params: [{ n: 'id', t: 'int', req: true, in: 'path', d: '回复 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "deleted": 15 } }'
        }
      ]
    },

    /* ---------------------------------------------------------------- 06 */
    {
      id: 'social', no: '06', name: 'social', zh: '关注关系',
      desc: 'Follow(from_user_id, to_user_id)。关注 / 取关 / 粉丝关注列表。(from, to) 唯一防重复关注，对方存在性经 identity.user_exists 校验。',
      endpoints: [
        {
          method: 'POST', path: '/api/follows', auth: 'login',
          desc: '关注某人。不能关注自己（400）；已关注幂等；对方不存在 NotFound。已软删则恢复。',
          params: [{ n: 'to_id', t: 'int', req: true, in: 'body', d: '被关注用户 id' }],
          reqBody: '{ "to_id": 7 }',
          res: '{ "errno": 0, "code": 201, "data": { "from_id": 42, "to_id": 7, "following": true } }'
        },
        {
          method: 'DELETE', path: '/api/follows/{to_id}', auth: 'login',
          desc: '取消关注。成功分支必须 return（修 CR #5）。软删。',
          cr: '修 CR #5 · 成功分支必须 return',
          params: [{ n: 'to_id', t: 'int', req: true, in: 'path', d: '被取关用户 id' }],
          reqBody: null,
          res: '{ "errno": 0, "code": 200, "data": { "from_id": 42, "to_id": 7, "following": false } }'
        },
        {
          method: 'GET', path: '/api/follows', auth: 'login',
          desc: '粉丝 / 关注列表（默认当前用户），带对方公开信息。',
          params: [
            { n: 'type', t: 'enum', req: true, in: 'query', d: 'fans | following' },
            { n: 'user_id', t: 'int', req: false, in: 'query', d: '默认当前用户' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": {\n    "items": [ { "id": 7, "nick_name": "小王", "avatar": "/media/images/default.jpg" } ],\n    "next_cursor": null, "count": 1\n  }\n}'
        }
      ]
    },

    /* ---------------------------------------------------------------- 07 */
    {
      id: 'search', no: '07', name: 'search', zh: '支撑域 · 全文检索',
      desc: '支撑域。目前仅 type=blog。参数化查询杜绝 SQL 注入（修 CR #2）：q 走 SQLAlchemy 绑定参数（Blog.content.like），优先经 content.service.search_blogs 组合。',
      support: true,
      endpoints: [
        {
          method: 'GET', path: '/api/search', auth: 'public',
          desc: '搜索博客。参数化查询，杜绝 SQL 注入（修 CR #2）。返回命中博客 + 作者信息。',
          cr: '修 CR #2 · 参数化查询防 SQL 注入',
          params: [
            { n: 'type', t: 'enum', req: true, in: 'query', d: '目前仅 blog' },
            { n: 'q', t: 'string', req: true, in: 'query', d: '关键词（绑定参数）' },
            { n: 'cursor', t: 'int', req: false, in: 'query', d: '游标' },
            { n: 'limit', t: 'int', req: false, in: 'query', d: '条数' }
          ],
          reqBody: null,
          res: '{\n  "errno": 0, "code": 200,\n  "data": {\n    "items": [\n      { "id": 77, "title": "今日 PR 更新",\n        "author": { "id": 42, "nick_name": "老李教练" } }\n    ],\n    "next_cursor": 76, "count": 1\n  }\n}'
        }
      ]
    },

    /* ---------------------------------------------------------------- 08 */
    {
      id: 'media', no: '08', name: 'media', zh: '支撑域 · 文件上传',
      desc: 'FileMap(md5, filename)。扩展名白名单 + Pillow 内容嗅探校验是图片；MD5 去重复用；随机文件名落盘（只写一次，修 CR #19）。',
      support: true,
      endpoints: [
        {
          method: 'POST', path: '/api/files', auth: 'login',
          desc: 'form-data media（可多文件）。扩展名白名单 + Pillow 内容嗅探；MD5 去重（命中 FileMap 复用 filename）；随机文件名落盘。只写一次盘（修 CR #19）。',
          cr: '修 CR #19 · 不重复写盘 + 内容嗅探校验',
          params: [{ n: 'media', t: 'file[]', req: true, in: 'form-data', d: '一个或多个图片文件' }],
          reqBody: 'Content-Type: multipart/form-data\n\nmedia=@plank.jpg\nmedia=@dl.jpg',
          res: '{\n  "errno": 0, "code": 201,\n  "data": {\n    "urls": [ "/media/images/a1b2c3.jpg", "/media/images/d4e5f6.jpg" ]\n  }\n}'
        }
      ]
    }
  ]
};
