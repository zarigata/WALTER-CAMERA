import cv2


class Display:
    def __init__(self, window_name: str = "Display", fullscreen: bool = True):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        if fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show(self, frame):
        cv2.imshow(self.window_name, frame)

    def poll_key(self, delay_ms: int = 1):
        return cv2.waitKey(delay_ms) & 0xFF

    def close(self):
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
