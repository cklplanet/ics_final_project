class Protocol:

    def __init__(self, bs=None):
        if bs:
            self.bs = bytearray(bs)
        else:
            self.bs = bytearray(0)

    def get_int32(self):
        try:
            ret = self.bs[4:]
            self.bs = self.bs[4:]
            return int.from_bytes(ret, byteorder='little')
        except:
            raise Exception("Error!")
    
    def get_str(self):
        try:
            length = int.from_bytes(self.bs[:2], byteorder='little')
            ret = self.bs[2:length + 2]
            self.bs = self.bs[2 + length:]
            return ret.decode(encoding='utf8')
        except:
            raise Exception("Error!")
    
    def add_int32(self, val):
        bytes_val = bytearray(val.to_bytes(4, byteorder='little'))
        self.bs += bytes_val

    def add_str(self, val):
        bytes_val = bytearray(val.encode(encoding='utf8'))
        bytes_length = bytearray(len(bytes_val).to_bytes(2, byteorder='little'))
        self.bs += (bytes_length + bytes_val)

    def get_pck_not_head(self):
        return self.bs

    def get_pck_has_head(self):
        bytes_pck_length = bytearray(len(self.bs).to_bytes(4, byteorder='little'))
        return bytes_pck_length + self.bs