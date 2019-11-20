from utils.generic_import import *


class ChallengeList(Resource):

    def get(self):
        response = Response()
        try:
            _id = request.args.get("id", 0)
            offset = request.args.get("page_offset", current_app.config["PAGE_OFFSET"])
            challenge_list = fetchall_dict(SelectMap.challenge_list_by_id, (_id, offset), GeneralObject)
            if not challenge_list:
                raise UserDoesNotExistException("id不存在")
            self._initial_title(challenge_list)
            response.data = {
                "count": len(challenge_list),
                "query_id": challenge_list[-1].id,
                "last_query_id": _id, "page_offset": offset,
                "challenge_list": [
                    challenge._items for challenge in challenge_list
                ]
            }
        except Exception as e:
            init_key_error_handler(response, e, "信息:")
        return jsonify(response.dict_data)

    def _get_title(self, challenge):
        soup = BeautifulSoup(challenge.content, "html.parser")
        length = current_app.config["TITLE_LENGTH"]
        return soup.text[:length+1] + "..."

    def _initial_title(self, challenge_list):
        for challenge in challenge_list:
            challenge.title = self._get_title(challenge)
