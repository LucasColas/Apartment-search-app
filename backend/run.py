import sys

# Must be set before uvicorn creates its event loop.
# SelectorEventLoop (Windows default) cannot spawn subprocesses,
# which Playwright requires. ProactorEventLoop can.
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
