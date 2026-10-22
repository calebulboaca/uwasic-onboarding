# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray
from cocotb.utils import get_sim_time

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(unit="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(unit="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")


async def wait_rising_edge(dut, timeout_cycles=7000):
    for _ in range(timeout_cycles):
        if not (int(dut.uo_out.value) & 1):
            break
        await ClockCycles(dut.clk, 1)
    else:
        assert False, "uo_out[0] stuck high, no falling edge seen"

    for _ in range(timeout_cycles):
        if int(dut.uo_out.value) & 1:
            return cocotb.utils.get_sim_time(unit="ns")
        await ClockCycles(dut.clk, 1)
    assert False, "uo_out[0] stuck low, no rising edge seen"

async def wait_falling_edge(dut, timeout_cycles=7000):
    for _ in range(timeout_cycles):
        if int(dut.uo_out.value) & 1:
            break
        await ClockCycles(dut.clk, 1)
    else:
        assert False, "uo_out[0] stuck low, no rising edge seen"

    for _ in range(timeout_cycles):
        if not (int(dut.uo_out.value) & 1):
            return cocotb.utils.get_sim_time(unit="ns")
        await ClockCycles(dut.clk, 1)
    assert False, "uo_out[0] stuck high, no falling edge seen"

@cocotb.test()
async def test_pwm_freq(dut):
    # Write your test here
    dut._log.info("Start PWM Frequency test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # Set registers to output pwm on bit 0 of uo_out
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    await send_spi_transaction(dut, 1, 0x04, 0x80) # 50% duty cycle

    posedge1_time = await wait_rising_edge(dut)
    posedge2_time = await wait_rising_edge(dut)

    period_ns = posedge2_time - posedge1_time
    freq_hz = 1e9 / period_ns

    dut._log.info(f"PWM frequency measured to be {freq_hz:.1f} Hz")
    assert 2970 <= freq_hz <= 3030, f"Frequency {freq_hz:.1f} Hz outside 3 kHz +-1%"
    
    dut._log.info("PWM Frequency test completed successfully")


async def assert_constant(dut, level, cycles=2 * 3334):
    for _ in range(cycles):
        assert (int(dut.uo_out.value) & 1) == level, \
            f"uo_out[0] changed from {level}, expected constant"
        await ClockCycles(dut.clk, 1)

@cocotb.test()
async def test_pwm_duty(dut):
    # Write your test here
    dut._log.info("Start PWM Duty Cycle test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # Set registers to output pwm on bit 0 of uo_out
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 0x01)


    # Sweep whole range except edge cases
    for duty in (0x01, 0x40, 0x80, 0xC0, 0xFE): 
        await send_spi_transaction(dut, 1, 0x04, duty)
        await ClockCycles(dut.clk, 3334)  # let a full period settle
        expected = duty / 256 * 100

        t_rise1 = await wait_rising_edge(dut)
        t_fall = await wait_falling_edge(dut)
        t_rise2 = await wait_rising_edge(dut)
        measured = (t_fall - t_rise1) / (t_rise2 - t_rise1) * 100

        dut._log.info(f"duty 0x{duty:02X}: expected {expected:.2f}%, measured {measured:.2f}%")
        assert abs(measured - expected) <= 1.0, \
            f"Duty 0x{duty:02X}: expected {expected:.2f}%, got {measured:.2f}%"

    # 100% duty cycle edge case
    await send_spi_transaction(dut, 1, 0x04, 0xFF)
    await ClockCycles(dut.clk, 3334)
    await assert_constant(dut, 1)

    # 0% duty cycle edge case
    await send_spi_transaction(dut, 1, 0x04, 0x00)
    await ClockCycles(dut.clk, 3334)
    await assert_constant(dut, 0)

    # Verify output enable = 0 overrides PWM enable = 1
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await send_spi_transaction(dut, 1, 0x00, 0x00)
    await ClockCycles(dut.clk, 3334)
    await assert_constant(dut, 0)

    # Verify output enabled + PWM disabled gives constant 1
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 0x00)
    await ClockCycles(dut.clk, 3334)
    await assert_constant(dut, 1)

    dut._log.info("PWM Duty Cycle test completed successfully")
