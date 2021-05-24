from utils import decimal_to_hex, get_current_seconds


def get_all_responses(arr):
    res = []
    for item in arr:
        content, is_valid = item.form_response()
        if is_valid:
            res.append(content)
    return "".join(res), len(res)


class Answer:
    def __init__(self, t, data, ttl):
        self._name = "c00c"
        self._type = t
        self._ttl = int(ttl, 16)
        self._data_len = len(data) // 2
        self._data = data

        self.valid_till = get_current_seconds() + self._ttl

    def form_response(self):
        return self._name + self._type + "0001" + \
               decimal_to_hex(self.valid_till - get_current_seconds()).rjust(8, '0') + \
               decimal_to_hex(self._data_len).rjust(4, '0') + self._data, self.valid_till > get_current_seconds()
