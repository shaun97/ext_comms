
import argparse
import os
from pynq import Overlay
import numpy as np
from pynq import allocate
import time
from finn.util.data_packing import (
    finnpy_to_packed_bytearray,
    packed_bytearray_to_finnpy
)
from finn.core.datatype import DataType
from pynq.ps import Clocks

class FINNAccelDriver():
    def __init__(self, N, bitfile, platform="zynq-iodma"):
        """Instantiate the FINN accelerator driver.
        Gets batchsize (N) as integer and path to bitfile as string."""
        self.platform = platform
        self.N = N
        # input FINN DataType
        self.idt = DataType.INT8
        # output FINN DataType
        self.odt = DataType.INT24
        # input and output shapes
        self.ishape_normal = (N, 168)
        self.oshape_normal = (N, 9)
        self.ishape_folded = (N, 1, 168)
        self.oshape_folded = (N, 1, 9)
        self.ishape_packed = (N, 1, 168)   # datatype np.uint8
        self.oshape_packed = (N, 1, 27)  # datatype np.uint8
        # load bitfile and set up accelerator
        self.ol = Overlay(bitfile)
        # neuron folding factor of output = iterations per sample
        self.itersPerSample = self.oshape_packed[-2]
        # clock frequency as specified by user
        self.fclk_mhz = 100.0
        if self.platform == "alveo":
            self.idma = self.ol.idma0
            self.odma = self.ol.odma0
        elif self.platform == "zynq-iodma":
            self.idma = self.ol.idma0
            self.odma = self.ol.odma0
            # set the clock frequency as specified by user during transformations
            if self.fclk_mhz > 0:
                Clocks.fclk0_mhz = self.fclk_mhz
        else:
            raise ValueError("Supported platforms are zynq-iodma alveo")

        # allocate a PYNQ buffer for the packed input and buffer
        if self.platform == "alveo":
            self.ibuf_packed_device = allocate(shape=self.ishape_packed, dtype=np.uint8)
            self.obuf_packed_device = allocate(shape=self.oshape_packed, dtype=np.uint8)
        else:
            self.ibuf_packed_device = allocate(shape=self.ishape_packed, dtype=np.uint8, cacheable=True)
            self.obuf_packed_device = allocate(shape=self.oshape_packed, dtype=np.uint8, cacheable=True)

    def fold_input(self, ibuf_normal):
        """Reshapes input in desired shape.
        Gets input data (ibuf_normal), checks if data is in expected normal shape.
        Returns folded input."""
        # ensure that shape is as expected
        assert ibuf_normal.shape == self.ishape_normal
        # convert to folded form
        ibuf_folded = ibuf_normal.reshape(self.ishape_folded)
        return ibuf_folded

    def pack_input(self, ibuf_folded):
        """Packs folded input and reverses both SIMD dim and endianness.
        Gets input data in folded shape and returns packed input data."""
        ibuf_packed = finnpy_to_packed_bytearray(
            ibuf_folded, self.idt, reverse_endian=True, reverse_inner=True
        )
        return ibuf_packed

    def unpack_output(self, obuf_packed):
        """Unpacks the packed output buffer from accelerator.
        Gets packed output and returns output data in folded shape."""
        obuf_folded = packed_bytearray_to_finnpy(
            obuf_packed, self.odt, self.oshape_folded, reverse_endian=True, reverse_inner=True
        )
        return obuf_folded

    def unfold_output(self, obuf_folded):
        """Unfolds output data to normal shape.
        Gets folded output data and returns output data in normal shape."""
        obuf_normal = obuf_folded.reshape(self.oshape_normal)
        return obuf_normal

    def copy_input_data_to_device(self, data):
        """Copies given input data to PYNQ buffer."""
        np.copyto(self.ibuf_packed_device, data)
        self.ibuf_packed_device.flush()

    def copy_output_data_from_device(self, data):
        """Copies PYNQ output buffer from device."""
        self.obuf_packed_device.invalidate()
        np.copyto(data, self.obuf_packed_device)

    def execute(self):
        """Executes accelerator by setting up the DMA(s) and
        waiting until all transfers/calls complete. Uses only member variables and
        returns nothing."""
        if self.platform == "zynq-iodma":
            # manually launch IODMAs since signatures are missing
            self.idma.write(0x10, self.ibuf_packed_device.device_address)
            self.idma.write(0x1c, self.N)
            self.odma.write(0x10, self.obuf_packed_device.device_address)
            self.odma.write(0x1c, self.N)
            self.idma.write(0x00, 1)
            self.odma.write(0x00, 1)
            # wait until output IODMA is finished
            status = self.odma.read(0x00)
            while status & 0x2 == 0:
                status = self.odma.read(0x00)
        elif self.platform == "alveo":
            idma_handle = self.idma.start_sw(self.ibuf_packed_device, self.N)
            odma_handle = self.odma.start_sw(self.obuf_packed_device, self.N)
            odma_handle.wait()

def infer_data_hardware(samples):
    exec_mode = "execute"
    platform = "zynq-iodma"
    N = 1
    bitfile = "resizer.bit"
    dance_move = ["zigzag","hair","rocket","shouldershrug","pushback","windowwipe","scarecrow","elbowlock", "logout"]
    print("infered hardware data")
    print("samples")
    print(samples)
    window = []
    for i, l in enumerate(samples):
        x = np.array(l)
        x = np.nan_to_num(x) 
        x = x.reshape(1, -1)
        for value in x[0]:
            window.append(value)
    window = np.array(window).astype('int8')
    print(window.dtype)
    # instantiate FINN accelerator driver and pass batchsize and bitfile
    finnDriver = FINNAccelDriver(N, bitfile, platform)
    print("numpy")
    # for the remote execution the data from the input npy file has to be loaded,
    # packed and copied to the PYNQ buffer
    if exec_mode == "execute":
        print(window)
        # load desired input .npy file
        ibuf_normal = window.reshape(1,168)
        ibuf_folded = finnDriver.fold_input(ibuf_normal)
        ibuf_packed = finnDriver.pack_input(ibuf_folded)
        finnDriver.copy_input_data_to_device(ibuf_packed)
    elif exec_mode != "throughput_test":
        raise Exception("Exec mode has to be set to remote_pynq or throughput_test")

    # execute accelerator
    finnDriver.execute()

    # if execution is selected unpack, unfold and save output to output npy file
    if exec_mode == "throughput_test":
        testing = 1
    else:
        obuf_packed = np.empty_like(finnDriver.obuf_packed_device)
        finnDriver.copy_output_data_from_device(obuf_packed)
        obuf_folded = finnDriver.unpack_output(obuf_packed)
        obuf_normal = finnDriver.unfold_output(obuf_folded)
        move = dance_move[np.argmax(obuf_normal)]
        print("executed, :move")
        print(move)

    return ["move", 42]

