from __future__ import annotations
import uvicorn
from .api.server import app


def run():
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
