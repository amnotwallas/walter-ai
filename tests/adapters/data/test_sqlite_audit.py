import pytest
import pytest_asyncio
import aiosqlite
from app.adapters.data.sqlite_audit import SqliteAuditAdapter


@pytest_asyncio.fixture
async def adapter(tmp_path):
    db_path = str(tmp_path / "test_audit.db")
    adapter = SqliteAuditAdapter(db_path=db_path)
    await adapter.init_db()
    yield adapter


@pytest.mark.asyncio
async def test_log_conversation(adapter):
    await adapter.log_conversation("id-1", "sess-1", "hola", "respuesta")
    async with aiosqlite.connect(adapter.db_path) as db:
        async with db.execute("SELECT query, response FROM conversations WHERE id='id-1'") as cursor:
            row = await cursor.fetchone()
    assert row == ("hola", "respuesta")


@pytest.mark.asyncio
async def test_log_tool_execution(adapter):
    await adapter.log_conversation("conv-1", "sess-1", "q", "r")
    await adapter.log_tool_execution("tool-1", "conv-1", "get_personal_info", "{}", "result", 42.5)
    async with aiosqlite.connect(adapter.db_path) as db:
        async with db.execute("SELECT tool_name, latency_ms FROM tool_executions WHERE id='tool-1'") as cursor:
            row = await cursor.fetchone()
    assert row == ("get_personal_info", 42.5)


@pytest.mark.asyncio
async def test_log_security_event(adapter):
    await adapter.log_security_event("ev-1", "length", "query muy largo...")
    async with aiosqlite.connect(adapter.db_path) as db:
        async with db.execute("SELECT reason FROM security_events WHERE id='ev-1'") as cursor:
            row = await cursor.fetchone()
    assert row == ("length",)


@pytest.mark.asyncio
async def test_get_anomalies_returns_dict(adapter):
    result = await adapter.get_anomalies()
    assert isinstance(result, dict)
    assert "high_failure_tools" in result


@pytest.mark.asyncio
async def test_get_anomalies_logic(adapter):
    # Setup standard and anomalous data to test the logic of get_anomalies
    
    # 1. High failure tool (e.g. error rate > 0.8)
    # Let's log some conversations
    await adapter.log_conversation("conv-1", "sess-1", "query1", "resp1")
    await adapter.log_conversation("conv-2", "sess-2", "query2", "resp2")
    
    # Tool 'bad_tool' has 100% error rate (result starts with 'Error')
    await adapter.log_tool_execution("t-1", "conv-1", "bad_tool", "{}", "Error: failed", 10.0)
    # Tool 'good_tool' has 0% error rate (result doesn't start with 'Error')
    await adapter.log_tool_execution("t-2", "conv-1", "good_tool", "{}", "Success", 10.0)
    
    # 2. Slow sessions
    # Total average latency of all tool_executions is: (10.0 + 10.0 + 100.0) / 3 = 40.0 ms.
    # An anomalous slow session needs total latency > AVG * 3. So session needs > 120 ms.
    # Let's add tool executions to sess-2 that total 150 ms (which is > 3 * AVG).
    await adapter.log_tool_execution("t-3", "conv-2", "good_tool", "{}", "Success", 150.0)
    
    # Calculate new average: (10 + 10 + 150) / 3 = 56.66 ms.
    # 3 * AVG = 170.0 ms. 150 is less than 170.
    # Let's make it more extreme:
    # Let's log a session that has a huge latency, e.g. 500 ms, while keeping other latencies low.
    # We log conv-3 in sess-3
    await adapter.log_conversation("conv-3", "sess-3", "query3", "resp3")
    await adapter.log_tool_execution("t-4", "conv-3", "slow_tool", "{}", "Success", 500.0)
    # Currently we have tool executions with latencies:
    # t-1 (bad_tool, conv-1/sess-1): 10.0
    # t-2 (good_tool, conv-1/sess-1): 10.0 (total sess-1: 20.0)
    # t-3 (good_tool, conv-2/sess-2): 150.0 (total sess-2: 150.0)
    # t-4 (slow_tool, conv-3/sess-3): 500.0 (total sess-3: 500.0)
    # Average latency = (10 + 10 + 150 + 500) / 4 = 167.5 ms
    # 3 * Average = 502.5 ms.
    # Total for sess-3 is 500.0, which is still <= 502.5 ms.
    # Let's add some more very small latency tools to bring the average down.
    await adapter.log_tool_execution("t-5", "conv-1", "good_tool", "{}", "Success", 5.0)
    await adapter.log_tool_execution("t-6", "conv-1", "good_tool", "{}", "Success", 5.0)
    # Now:
    # t-1: 10
    # t-2: 10
    # t-3: 150
    # t-4: 500
    # t-5: 5
    # t-6: 5
    # Total tools: 6, Sum = 680 ms, Average = 113.33 ms.
    # 3 * Average = 340 ms.
    # sess-3 has total latency 500 ms, which is > 340 ms. So sess-3 should be classified as slow_sessions.
    
    # 3. Slow tools (ordered by avg latency DESC)
    # Average latencies per tool:
    # slow_tool: 500 ms (1 execution)
    # good_tool: (10 + 150 + 5 + 5) / 4 = 42.5 ms (4 executions)
    # bad_tool: 10 ms (1 execution)
    
    result = await adapter.get_anomalies()
    
    assert "bad_tool" in result["high_failure_tools"]
    assert "good_tool" not in result["high_failure_tools"]
    
    assert "sess-3" in result["slow_sessions"]
    assert "sess-1" not in result["slow_sessions"]
    
    assert result["slow_tools"][0]["tool"] == "slow_tool"
    assert result["slow_tools"][0]["avg_ms"] == 500.0
    assert result["slow_tools"][1]["tool"] == "good_tool"
    assert result["slow_tools"][1]["avg_ms"] == 42.5
