import asyncio
import sys

import pytest

from async_interrupt import _Interrupt, interrupt


@pytest.mark.asyncio
async def test_interrupt_immediate():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    with pytest.raises(ValueError, match="message"):
        async with interrupt(future, ValueError, "message"):
            future.set_result(None)
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_interrupt_immediate_no_message():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    with pytest.raises(ValueError):
        async with interrupt(future, ValueError, None):
            future.set_result(None)
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_interrupt_soon():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    with pytest.raises(ValueError, match="message"):
        async with interrupt(future, ValueError, "message"):
            loop.call_soon(future.set_result, None)
            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_interrupt_later():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    with pytest.raises(ValueError, match="message"):
        async with interrupt(future, ValueError, "message"):
            loop.call_later(0.001, future.set_result, None)
            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_interrupt_does_not_happen():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    async with interrupt(future, ValueError, "message"):
        await asyncio.sleep(0.001)


@pytest.mark.asyncio
async def test_interrupt_does_not_happen_after_context_exit():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    loop.call_soon(future.set_result, None)

    async with interrupt(future, ValueError, "message"):
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_reuse_not_allowed():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    loop.call_soon(future.set_result, None)
    manual_interrupt = _Interrupt(loop, future, ValueError, "message")

    async with manual_interrupt:
        await asyncio.sleep(0)

    with pytest.raises(RuntimeError):
        async with manual_interrupt:
            await asyncio.sleep(0)


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="py3.11 is the first version to support uncancel()",
)
@pytest.mark.asyncio
async def test_interrupt_with_current_task_canceled():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    with pytest.raises(asyncio.CancelledError):
        async with interrupt(future, ValueError, "message"):
            if task := asyncio.current_task():
                task.cancel("external cancel")
            future.set_result(None)
            await asyncio.sleep(1)
