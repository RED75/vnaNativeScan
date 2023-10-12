class VNARequestBuilder:
    _MAX_AVERAGES: int = 16
    _MIN_AVERAGES: int = 0
    _MAX_STEPS: int = 10_000
    _MIN_STEPS: int = 1
    _MIN_F_STEP: int = 1

    base_template = bytearray.fromhex("40 06 91 01 03 01 10 00 98 92 98 00 00 00 00 00 05 00 00 00 00 00 00 00")

    base_template_desctiption = """40 06 (E8 03)->(n steps) 03 (01)-(n averages) 10 (00 80 96 98)->f_start 00 00 (00 00 00 01)->(step in hz) 00 00 00 00 00 00 00 
    10000000 1000 0 10001000"""

    parameters: list[str] = ["n_steps", "n_averages", "f_start", "f_step"]

    offsets = {parameters[0]: 2, parameters[1]: 5, parameters[2]: 8, parameters[3]: 16}
    lengths = {parameters[0]: 2, parameters[1]: 1, parameters[2]: 4, parameters[3]: 4}
    values = {parameters[0]: 0, parameters[1]: 0, parameters[2]: 0, parameters[3]: 0}

    def __init__(self, F_start: int = 10_000_000, F_stop: int = 10_001_000, n_steps: int = 1000, averages: int = 10):
        self.parameters: list[str] = ["n_steps", "n_averages", "f_start", "f_step"]

        self.offsets = {self.parameters[0]: 2, self.parameters[1]: 5, self.parameters[2]: 8, self.parameters[3]: 16}
        self.lengths = {self.parameters[0]: 2, self.parameters[1]: 1, self.parameters[2]: 4, self.parameters[3]: 4}
        self.values = {self.parameters[0]: 0, self.parameters[1]: 0, self.parameters[2]: 0, self.parameters[3]: 0}

        self.F_step: int = max(int((F_stop - F_start) / n_steps), VNARequestBuilder._MIN_F_STEP)
        self.F_start = F_start
        self.n_steps = max(min(n_steps, VNARequestBuilder._MAX_STEPS), VNARequestBuilder._MIN_STEPS)
        self.n_averages = max(min(averages, VNARequestBuilder._MAX_AVERAGES), VNARequestBuilder._MIN_AVERAGES)

        self.values["n_steps"] = self.n_steps
        self.values["n_averages"] = self.n_averages
        self.values["f_start"] = self.F_start
        self.values["f_step"] = self.F_step

    def makeRequestArray(self):
        pass

    def set_F_start(self, F_start: int):
        self.F_start = F_start
        return self

    def get_codes(self):
        generated_pattern = VNARequestBuilder.base_template.copy()
        for k, v in self.offsets.items():
            generated_pattern = VNARequestBuilder.insert_int_into_bytearray(generated_pattern, v, self.values[k],
                                                                            self.lengths[k])
        return generated_pattern

    @staticmethod
    def insert_int_into_bytearray(arr: bytearray, offset: int, value: int, length: int, order: str = "little"):
        # print("before", arr, offset, value, length, order)
        arr[offset:offset + length] = value.to_bytes(length=length, byteorder=order)
        # print("after:",arr, offset, value, length, order)
        return arr