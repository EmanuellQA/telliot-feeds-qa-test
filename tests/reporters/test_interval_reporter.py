"""
Tests covering the IntervalReporter class from
telliot's reporters subpackage.
"""
import pytest

from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.reporters.interval import IntervalReporter
from tests.conftest import reporter_submit_once


@pytest.fixture
def eth_usd_reporter(rinkeby_cfg, master, oracle):
    """Returns an instance of an IntervalReporter using
    the ETH/USD median datafeed."""
    r = IntervalReporter(
        endpoint=rinkeby_cfg.get_endpoint(),
        private_key=rinkeby_cfg.main.private_key,
        master=master,
        oracle=oracle,
        datafeed=eth_usd_median_feed,
    )
    return r


@pytest.mark.asyncio
async def test_ensure_staked(eth_usd_reporter):
    """Test staking status of reporter."""
    staked, status = await eth_usd_reporter.ensure_staked(gas_price_gwei=10)

    assert staked
    assert status.ok


@pytest.mark.asyncio
async def test_check_reporter_lock(eth_usd_reporter):
    """Test checking if in reporter lock."""
    r = eth_usd_reporter

    assert r.last_submission_timestamp == 0

    reporter_locked, status = await r.check_reporter_lock()

    assert reporter_locked
    assert not status.ok
    assert status.error == "Current address is in reporter lock."
    assert r.last_submission_timestamp != 0


@pytest.mark.asyncio
async def test_enforce_gas_price_limit(eth_usd_reporter):
    """Test max gas price limit."""
    r = eth_usd_reporter

    assert r.max_gas_price == 0

    r.max_gas_price = 10
    gas_price_below_limit, status = await r.enforce_gas_price_limit(gas_price_gwei=1e10)

    assert not gas_price_below_limit
    assert not status.ok
    assert status.error == "Estimated gas price is above maximum gas price."


@pytest.mark.asyncio
async def test_ensure_profitable(eth_usd_reporter):
    """Test profitability check."""
    r = eth_usd_reporter

    assert r.profit_threshold == 0

    profitable, status = await r.ensure_profitable(gas_price_gwei=10)

    assert profitable
    assert status.ok

    r.profit_threshold = 1e10
    profitable, status = await r.ensure_profitable(gas_price_gwei=10)

    assert not profitable
    assert not status.ok
    assert status.error == "Estimated profitability below threshold."


@pytest.mark.asyncio
async def test_interval_reporter_submit_once(rinkeby_cfg, master, oracle):
    """Test reporting once to the TellorX playground on Rinkeby
    with three retries."""

    await reporter_submit_once(rinkeby_cfg, master, oracle, eth_usd_median_feed)
