class Session:
    def __init__(self, uid: int, current_dir, id: int) -> None:
        self.real_uid = uid
        self.effective_uid = uid
        self.id = id

        self.current_dir = current_dir

        self.env = {}
