# SIMULATION DEPENDENCY GUIDE

This guide records the dependency structure of the simulator as a scientific modeling pipeline.

## 1. Overall Execution Flow

Neural network model
↓
Quantization and activation modeling
↓
Behavioral mapping
↓
Tile-connection graph construction
↓
Device-level parameterization
↓
Crossbar-level analog computation model
↓
Peripheral DAC/ADC abstraction
↓
Processing element abstraction
↓
Tile abstraction
↓
Latency / power / energy / area estimation
↓
Accuracy modeling
↓
Final statistics

## 2. Module Dependency Graph

### Device model
- Provides electrical primitives to the crossbar model
- Uses configuration values from the hardware description file
- Supplies resistance-state and voltage abstractions for analog computation

- [MNSIM-2.0/MNSIM/Interface/network.py](MNSIM-2.0/MNSIM/Interface/network.py)
  - produces the neural network structure and tensor-level computational graph
- [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py)
  - quantizes weights and activations for PIM-style computation
- [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py)
  - maps the network graph onto hardware resources
- [MNSIM-2.0/MNSIM/Mapping_Model/Tile_connection_graph.py](MNSIM-2.0/MNSIM/Mapping_Model/Tile_connection_graph.py)
  - constructs tile connectivity and communication structure
- [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py)
  - defines resistance, voltage, latency, and energy primitives
- [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py)
  - models analog computation and crossbar costs
- [MNSIM-2.0/MNSIM/Hardware_Model/ADC.py](MNSIM-2.0/MNSIM/Hardware_Model/ADC.py)
  - models analog-to-digital conversion
- [MNSIM-2.0/MNSIM/Hardware_Model/DAC.py](MNSIM-2.0/MNSIM/Hardware_Model/DAC.py)
  - models digital-to-analog conversion
- [MNSIM-2.0/MNSIM/Hardware_Model/PE.py](MNSIM-2.0/MNSIM/Hardware_Model/PE.py)
  - aggregates crossbar and peripheral blocks into a processing element
- [MNSIM-2.0/MNSIM/Hardware_Model/Tile.py](MNSIM-2.0/MNSIM/Hardware_Model/Tile.py)
  - aggregates multiple PEs into a tile
- [MNSIM-2.0/MNSIM/Latency_Model](MNSIM-2.0/MNSIM/Latency_Model)
  - estimates total latency
- [MNSIM-2.0/MNSIM/Power_Model](MNSIM-2.0/MNSIM/Power_Model)
  - estimates total power
- [MNSIM-2.0/MNSIM/Energy_Model](MNSIM-2.0/MNSIM/Energy_Model)
  - estimates total energy
- [MNSIM-2.0/MNSIM/Area_Model](MNSIM-2.0/MNSIM/Area_Model)
  - estimates total area
- [MNSIM-2.0/MNSIM/Accuracy_Model](MNSIM-2.0/MNSIM/Accuracy_Model)
  - estimates accuracy degradation under device non-idealities

## 3. Mathematical Dependency Graph

- Neural-network layer structure
  → quantized representation
  → mapped hardware resources
  → crossbar conductance states
  → peripheral ADC/DAC conversions
  → PE-level accumulation
  → tile-level aggregation
  → system-level performance metrics

## 4. Hardware Dependency Graph

- Device primitives
  → crossbar model
  → PE model
  → tile model
  → system-level estimators

## 5. PIM Dependency Graph

- Weight storage in resistive states
  → analog computation through voltage/current accumulation
  → ADC conversion
  → digital accumulation and output generation

## 6. Current Status

- The neural-network, quantization, mapping, and performance-estimation layers have been incorporated into the scientific reconstruction.
- The guide now reflects the full simulator pipeline from network abstraction to hardware cost evaluation.
