# MASTER MATHEMATICAL MODEL

This document records the scientific and mathematical model reconstructed from the simulator. It is intended for use in the methodology section of a technical report or research paper.

## Status

- Analyzed files: 5/18
- Current focus: [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py), [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py), and [MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py](MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py)
- Document purpose: to provide a traceable methodology narrative rather than a software-oriented code summary

---

## 1. Global Simulation Context

The simulator models a memristive crossbar-based processing-in-memory architecture for neural network inference. The mathematical framework combines:

1. Neural-network computation through quantized weights and activations.
2. Conductance-based representation of memristive devices.
3. Crossbar-level analog dot-product approximation.
4. Peripheral interface modeling through DAC/ADC abstractions.
5. System-level estimation of area, latency, power, and energy.

### 1.1 Traceability and review conventions

To make the reconstruction suitable for a research paper and for mentor review, each equation in this document is classified as follows:

- Directly implemented in code: the equation is explicitly present in the implementation logic.
- Derived from implementation: the equation is not written literally but follows from the loops, accumulations, or control flow in the code.
- Approximation: the equation is a reduced-order analytical abstraction used to estimate a quantity.

Each equation is also linked to the originating file and function where possible.

### 1.2 Mathematical dependency tree

The simulator can be read as a mathematical pipeline:

Resistance

↓

Conductance

↓

Crossbar current and power

↓

Read/write energy

↓

ADC and digital accumulation

↓

PE/tile aggregation

↓

Latency, power, area, and accuracy

This dependency tree is the mathematical counterpart of the software dependency chain.

---

## 2. Module 1: Crossbar Model

### 2.1 Purpose

The crossbar model represents the physical substrate on which analog matrix-vector multiplication is approximated. Its role is to translate a stored weight matrix into a conductance matrix and estimate the resulting physical cost of read and write operations.

### 2.2 Mathematical Role

The crossbar module introduces the first physically interpretable hardware abstraction in the simulator. It converts the abstract weight matrix into an electrical formulation governed by device resistance, voltage, and circuit-level scaling laws.

### 2.3 Governing Equations

#### Equation (1): Crossbar utilization

$$
U = \frac{N_r^{\mathrm{used}} N_c^{\mathrm{used}}}{R C}
$$

where:
- $U$ is the crossbar utilization factor,
- $N_r^{\mathrm{used}}$ is the number of active rows,
- $N_c^{\mathrm{used}}$ is the number of active columns,
- $R$ is the total number of rows,
- $C$ is the total number of columns.

#### Equation (2): Conductance representation of a stored weight

$$
G_{ij} = \frac{1}{R_{ij}}
$$

where:
- $G_{ij}$ is the conductance of the cell at row $i$ and column $j$,
- $R_{ij}$ is the programmed resistance of that cell.

#### Equation (3): Read power of the crossbar

$$
P_{\mathrm{read}} = \sum_{i=1}^{R}\sum_{j=1}^{C} G_{ij} v_i^2
$$

where:
- $v_i$ is the input voltage applied to row $i$.

This is the analog read power model used by the simulator.

#### Equation (4): Write power of the crossbar

$$
P_{\mathrm{write}} = \frac{1}{N_r^{\mathrm{write}}} \sum_{i=1}^{N_r^{\mathrm{write}}}\sum_{j=1}^{N_c^{\mathrm{write}}} G_{ij}^{w} (v_i^{w})^2
$$

where:
- $G_{ij}^{w}$ is the conductance during write programming,
- $v_i^{w}$ is the write voltage applied at row $i$.

#### Equation (5): Device-level electrical power relation

$$
P = \frac{V^2}{R}
$$

This is the constitutive electrical model from which both read and write power are derived.

#### Equation (6): Crossbar area model

$$
A_{\mathrm{xbar}} = A_{\mathrm{cell}} R C + A_{\mathrm{driver}} R
$$

The simulator implements several practical variants of this basic formulation.

#### Equation (7): Area variant A

$$
A_{\mathrm{xbar}} = A_{\mathrm{cell}} R C + R \left(7.3\cdot2.7 + 9.5\cdot3.8\right) \left(\frac{T_{\mathrm{tr}}}{65}\right)^2
$$

#### Equation (8): Area variant B

$$
A_{\mathrm{xbar}} = A_{\mathrm{cell}} R C + 1150 R
$$

#### Equation (9): Area variant C (simplified)

$$
A_{\mathrm{xbar}} = 5RC
$$

#### Equation (10): Area variant D (technology-scaled)

$$
A_{\mathrm{xbar}} = 4 R C T_{\mathrm{tech}}^2 \times 10^{-6}
$$

for cells of type beginning with `0`, and

$$
A_{\mathrm{xbar}} = 3(W/L + 1)RC T_{\mathrm{tech}}^2 \times 10^{-6}
$$

for the alternative case.

#### Equation (11): Wire-delay scaling fit

$$
S = \frac{RC}{1024\cdot 8}
$$

$$
T_{\mathrm{wire}} = 10^{-3}\left(2\times10^{-4}S^2 + 5\times10^{-6}S + 4\times10^{-14}\right)
$$

#### Equation (12): Read latency

$$
T_{\mathrm{read}} = T_{\mathrm{dev,read}} + T_{\mathrm{wire}}
$$

#### Equation (13): Write latency

$$
T_{\mathrm{write}} = T_{\mathrm{dev,write}} N_r^{\mathrm{write}}
$$

#### Equation (14): Read energy

$$
E_{\mathrm{read}} = P_{\mathrm{read}} T_{\mathrm{read}}
$$

#### Equation (15): Write energy

$$
E_{\mathrm{write}} = P_{\mathrm{write}} T_{\mathrm{write}}
$$

### 2.4 Assumptions

- The crossbar is modeled as a homogeneous array of identical cells.
- Weights are represented as resistive states.
- The analog operation is approximated by conductance-based electrical power dissipation.
- The write operation is assumed to occur row-wise.
- Wire delay is represented by a fitted polynomial rather than a detailed distributed RC model.
- Peripheral overhead is represented by simple scaling terms.

### 2.5 Scientific Interpretation

The module introduces a reduced-order physical model of a crossbar array. It does not simulate device physics in full detail; rather, it approximates macroscopic power, delay, area, and energy using conductance, voltage, and geometry-based scaling laws.

### 2.6 Equation provenance and dependencies

| Equation | Type | Implemented in | Theoretical origin | Dependency chain | Used by |
|---|---|---|---|---|---|
| Eq. (1) | Derived from implementation | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), xbar_write_config/xbar_read_config | Utilization ratio | None | Later area and utilization estimates |
| Eq. (2) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py) | Conductance definition | Device resistance | Crossbar power |
| Eq. (3) | Derived from nested loops | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_read_power | Ohm’s law and Kirchhoff-style accumulation | Conductance | Read energy |
| Eq. (4) | Derived from nested loops | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_write_power | Analog write power accumulation | Conductance | Write energy |
| Eq. (5) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_read_power | Ohm’s law | Resistance, voltage | Crossbar power |
| Eq. (6) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_area | Geometric area scaling | Crossbar dimensions | Tile area |
| Eq. (11) | Approximation | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_read_latency | Polynomial wire-delay fit | Crossbar size | Read latency |
| Eq. (12) | Derived from implementation | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_read_latency | Delay decomposition | Device latency + wire delay | Energy |
| Eq. (13) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), calculate_xbar_write_latency | Row-wise write timing | Device write latency | Write energy |
| Eq. (14)–(15) | Derived from implementation | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py) | Power-latency relation | Power + latency | System energy |

---

## 3. Module 2: Device Model

### 3.1 Purpose

The device model provides the elementary electrical and reliability parameters that define the behavior of the memory element used in the crossbar. In the simulator, this module is not a full semiconductor-device physics model. Instead, it defines a reduced-order analytical abstraction for a memristive or SRAM cell in terms of resistance, voltage, latency, power, and variation.

### 3.2 Dependency Chain

- Previous conceptual stage: hardware configuration and mapping specification
- Current module: Device model
- Next module: Crossbar model

The crossbar model inherits this module and uses its resistance states and voltage levels to define conductance and power.

### 3.3 Inputs

| Variable | Meaning | Units | Source |
|---|---|---|---|
| $R_0, R_1$ | Low and high resistance states of the device | $\Omega$ | Configuration file |
| $L$ | Number of discrete resistance levels | dimensionless | Configuration file |
| $V_{\mathrm{read},0}, V_{\mathrm{read},1}$ | Lower and upper read-voltage levels | V | Configuration file |
| $V_{\mathrm{write},0}, V_{\mathrm{write},1}$ | Lower and upper write-voltage levels | V | Configuration file |
| $T_{\mathrm{read}}$ | Read latency | ns | Configuration file |
| $T_{\mathrm{write}}$ | Write latency | ns | Configuration file |
| $E_{\mathrm{read}}^{\mathrm{cfg}}$ | SRAM read energy from configuration | J | Configuration file |
| $E_{\mathrm{write}}^{\mathrm{cfg}}$ | SRAM write energy from configuration | J | Configuration file |
| $\eta$ | Relative device variation | dimensionless | Configuration file |
| $A_{\mathrm{dev}}$ | Device area | $\mu m^2$ | Configuration file |

### 3.4 Outputs

| Output | Meaning | Used By |
|---|---|---|
| $R_{\mathrm{eff}}$ | Effective resistance used for power estimation | Crossbar model |
| $V_{\mathrm{read}}$ | Effective read voltage | Crossbar model |
| $V_{\mathrm{write}}$ | Effective write voltage | Crossbar model |
| $P_{\mathrm{read}}^{\mathrm{dev}}$ | Device read power | Crossbar model |
| $P_{\mathrm{write}}^{\mathrm{dev}}$ | Device write power | Crossbar model |
| $\mathcal{R}$ | Resistance-state set | Crossbar model |

### 3.5 Mathematical Models

#### Equation (17): Resistance-state set

$$
\mathcal{R} = \{R_0, R_1, \dots, R_{L-1}\}
$$

where $L$ is the number of discrete resistance levels.

#### Equation (18): Relative device variation

$$
\eta = \frac{\Delta R}{R}
$$

This represents the relative spread of the resistance state.

#### Equation (19): Effective read resistance for a memristive cell

$$
R_{\mathrm{eff}}^{(r)} = \frac{R_0 R_1}{0.67 R_1 + 0.33 R_0}
$$

This is a weighted harmonic-type effective resistance approximation.

#### Equation (20): Effective read voltage

$$
V_{\mathrm{read}} = \sqrt{0.9 V_{\mathrm{read},0}^2 + 0.1 V_{\mathrm{read},1}^2}
$$

This is a weighted root-mean-square voltage estimate.

#### Equation (21): Device read power

$$
P_{\mathrm{read}}^{\mathrm{dev}} = \frac{V_{\mathrm{read}}^2}{R_{\mathrm{eff}}^{(r)}}
$$

#### Equation (22): Effective write resistance

$$
R_{\mathrm{eff}}^{(w)} = \sqrt{R_0 R_1}
$$

This is the geometric-mean approximation used for write-state estimation.

#### Equation (23): Effective write voltage

$$
V_{\mathrm{write}} = \frac{V_{\mathrm{write},0} + V_{\mathrm{write},1}}{2}
$$

#### Equation (24): Device write power

$$
P_{\mathrm{write}}^{\mathrm{dev}} = \frac{V_{\mathrm{write}}^2}{R_{\mathrm{eff}}^{(w)}}
$$

#### Equation (25): SRAM power from configured energy and latency

$$
P_{\mathrm{read}}^{\mathrm{dev}} = \frac{E_{\mathrm{read}}^{\mathrm{cfg}}}{T_{\mathrm{read}}}
$$

$$
P_{\mathrm{write}}^{\mathrm{dev}} = \frac{E_{\mathrm{write}}^{\mathrm{cfg}}}{T_{\mathrm{write}}}
$$

### 3.6 Algorithm

1. Load the device configuration.
2. Determine whether the device is modeled as NVM or SRAM.
3. For NVM, define the resistance-state set and quantized variation parameter.
4. Compute an effective resistance and an effective voltage for read and write operations.
5. Convert those values into device-level power estimates using the electrical power law.
6. For SRAM, use configured energy values to assign read/write power via division by latency.

### 3.7 Code to Mathematics Mapping

| Code expression | Mathematical meaning |
|---|---|
| $V^2 / R$ | Ohm-law-based electrical power |
| $\sqrt{0.9V_0^2 + 0.1V_1^2}$ | weighted RMS voltage |
| $(R_0R_1)/(0.67R_1 + 0.33R_0)$ | weighted harmonic-type effective resistance |
| $\sqrt{R_0R_1}$ | geometric-mean resistance |
| $(V_0 + V_1)/2$ | arithmetic mean voltage |
| $E/T$ | power from energy and latency |

### 3.8 Assumptions

- The device is modeled as a single lumped resistive element.
- The read and write behavior is represented by a small number of effective parameters.
- The effect of variation is captured as a relative resistance spread.
- The read and write voltages are represented by scalar effective values rather than full waveform dynamics.
- The model assumes no detailed parasitic or thermal behavior.

### 3.9 Scientific Contribution

This file introduces the first electrical primitive of the simulator. It converts the abstract hardware description into a physically interpretable device-level model based on resistance, voltage, and power.

### 3.10 Dependency on Previous Mathematical Models

This module does not introduce network-level computation; instead, it provides the electrical primitives used by the crossbar model. It is the basis for the later conductance-power equations.

### 3.11 Equation provenance and dependencies

| Equation | Type | Implemented in | Theoretical origin | Dependency chain | Used by |
|---|---|---|---|---|---|
| Eq. (17) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py) | Resistance-state definition | Configuration input | Conductance mapping |
| Eq. (18) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py) | Relative variation | Device configuration | Non-ideal resistance modeling |
| Eq. (19) | Approximation | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_read_power | Weighted harmonic-type effective resistance | Resistance states | Read power |
| Eq. (20) | Approximation | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_read_power | Weighted RMS voltage | Voltage levels | Read power |
| Eq. (21) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_read_power | Ohm’s law | Effective resistance + voltage | Crossbar read power |
| Eq. (22) | Approximation | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_write_power | Geometric-mean resistance | Resistance states | Write power |
| Eq. (23) | Approximation | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_write_power | Arithmetic mean voltage | Write voltage levels | Write power |
| Eq. (24) | Directly implemented | [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py), calculate_device_write_power | Ohm’s law | Effective resistance + voltage | Crossbar write power |

---

## 4. Module 4: Neural-Network Quantization and PIM Computation

### 4.1 Purpose

The quantization layer translates the abstract neural network into a hardware-compatible computational form. The simulator models both the numerical quantization of weights and activations and the pseudo-analog operation performed by the crossbar fabric.

### 4.2 Mathematical Role

The neural-network interface is not treated as a conventional floating-point execution graph. Instead, each layer is converted into a discretized representation with bounded dynamic range, and the resulting values are processed by a bit-sliced analog dot-product approximation.

### 4.3 Quantization Model

Let $x$ be an input tensor and $w$ a weight tensor. The simulator uses a uniform quantization law of the form

$$
q(x;b,s) = \mathrm{clip}\left(\mathrm{round}\left(\frac{x}{s} \, \theta_b \right),\,-\theta_b,\,\theta_b-0\right)\frac{s}{\theta_b},
$$

where

$$
\theta_b = 2^{b-1}-1,
$$

$b$ is the quantization bit-width, and $s$ is the scaling factor.

For weights, the simulator uses a scale based on the maximal magnitude,

$$
s_w = \max(|w|),
$$

and the quantized weight is therefore

$$
\hat{w} = q(w;b_w,s_w).
$$

For activations, the simulator uses an adaptive scale based on a running estimate of the activation statistics,

$$
s_a^{(t)} = \rho s_a^{(t-1)} + (1-\rho)\left(3\sigma_a^{(t)} + |\mu_a^{(t)}|\right),
$$

with $\rho = 0.707$ in the implementation. The activation quantization then becomes

$$
\hat{x} = q(x;b_a,s_a^{(t)}).
$$

### 4.4 Bit-Sliced Crossbar Computation

The simulator decomposes the input activation and the stored weight into bit planes. If

$$
x = \sum_{p=0}^{B_a-1} x_p 2^p,
$$

and

$$
w = \sum_{q=0}^{B_w-1} w_q 2^q,
$$

then the analog multiply-accumulate operation is approximated as a sum of partial products,

$$
y \approx \sum_{p,q} \left( x_p \otimes w_q \right) 2^{p+q},
$$

where $\otimes$ denotes the analog crossbar multiply implemented through conductance-based accumulation.

The simulator also introduces a crossbar-specific scaling term to recover the output magnitude at the ADC boundary. In effect, the computation is represented as

$$
y_{\mathrm{ADC}} = \mathrm{round}\left( y \cdot 2^{\tau} \right),
$$

where $\tau$ is a transfer-point shift determined by the number of bit-slices and ADC precision.

### 4.5 Crossbar-Splitting Geometry

For convolution layers, the simulator partitions the input channels across crossbars according to the xbar row capacity. If the kernel size is $k$, then the number of channels that fit into one crossbar is

$$
C_{\mathrm{xbar}} = \left\lfloor \frac{\text{xbar\_size}}{k^2} \right\rfloor.
$$

The corresponding ADC bit-width extension is

$$
\Delta b_{\mathrm{ADC}} = \max\left(\left\lceil \log_2\left(\frac{C_{\mathrm{xbar}}k^2}{\text{DAC\_num}}\right) \right\rceil, 0\right).
$$

For fully connected layers, the split size is simply

$$
C_{\mathrm{xbar}} = \text{xbar\_size}.
$$

### 4.6 Interpretation

This layer converts the neural network into a physically realizable algebra over quantized values and crossbar bit-planes. The key idea is that the simulator does not attempt full numerical precision; it uses a reduced-order, discretized, analog-friendly approximation of the layer computation.

### 4.7 Equation provenance and dependencies

| Equation | Type | Implemented in | Theoretical origin | Dependency chain | Used by |
|---|---|---|---|---|---|
| Quantization law | Derived from implementation | [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py), QuantizeFunction.forward | Uniform quantization | Input tensor and scale | Weight/activation discretization |
| Bit-slice decomposition | Derived from implementation | [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py), QuantizeLayer.forward | Binary decomposition | Quantized values | Crossbar-style accumulation |
| ADC bit-extension term | Directly implemented | [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py) | Bit-width extension from channel splitting | Crossbar row/column split | ADC precision planning |

---

## 5. Module 5: Behavioral Mapping and Resource Allocation

### 5.1 Purpose

The behavioral mapping layer determines how each layer of the network is assigned to hardware resources such as PEs, tiles, and crossbars.

### 5.2 Layer-Level Cost Expressions

For a convolution layer, the simulator defines:

$$
L_{\mathrm{kernel}} = k^2 C_{\mathrm{in}},
$$

$$
S_{\mathrm{slide}} = H_{\mathrm{out}} W_{\mathrm{out}},
$$

and the number of multiply-accumulate operations is approximated by

$$
N_{\mathrm{op}} = 2 \, S_{\mathrm{slide}} \, L_{\mathrm{kernel}} \, C_{\mathrm{out}}.
$$

For a fully connected layer, it uses

$$
N_{\mathrm{op}} = 2 \times N_{\mathrm{in}} \times N_{\mathrm{out}}.
$$

### 5.3 PE and Tile Allocation

The simulator forms a resource requirement based on the channel and precision dimensions. Let

$$
C_{\mathrm{in,xbar}} = \min\left(\frac{\text{xbar\_row}}{k^2}, C_{\mathrm{in}}\right),
$$

and

$$
C_{\mathrm{out,xbar}} = \min\left(C_{\mathrm{out}}, \text{xbar\_column}\right).
$$

Then the number of PEs required for a layer is estimated as

$$
N_{\mathrm{PE}} = \left\lceil \frac{C_{\mathrm{in}}}{C_{\mathrm{in,xbar}}} \right\rceil
\left\lceil \frac{C_{\mathrm{out}}}{C_{\mathrm{out,xbar}}} \right\rceil
\left\lceil \frac{b_w^{\mathrm{eff}}}{b_{\mathrm{PE}}} \right\rceil,
$$

where $b_w^{\mathrm{eff}}$ is the effective weight precision after considering polarity and $b_{\mathrm{PE}}$ is the PE bit-width capacity.

The number of tiles required is

$$
N_{\mathrm{tile}} = \left\lceil \frac{N_{\mathrm{PE}}}{N_{\mathrm{PE}}^{\mathrm{tile}}} \right\rceil.
$$

### 5.4 Mapping Geometry

The mapping procedure partitions the layer tensor along three dimensions:

1. kernel-length dimension,
2. output-channel dimension,
3. weight-precision dimension.

Each partition is assigned to a PE tile group, and the simulator records the occupied row and column dimensions as read-row and read-column tuples. This produces a hardware occupancy representation that later feeds latency and power estimation.

### 5.5 Interpretation

This stage is the bridge between a neural-network graph and a hardware resource graph. It turns a logical layer structure into a set of crossbar and PE allocations, which are then used to estimate area, latency, power, and energy.

### 5.6 Equation provenance and dependencies

| Equation | Type | Implemented in | Theoretical origin | Dependency chain | Used by |
|---|---|---|---|---|---|
| $N_{\mathrm{op}}$ | Derived from implementation | [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py), config_behavior_mapping | Layer-wise arithmetic intensity | Layer shape and channels | Resource count |
| $N_{\mathrm{PE}}$ | Derived from implementation | [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py), config_behavior_mapping | Partitioning over rows, columns, and precision | Crossbar geometry | Tile count |
| $N_{\mathrm{tile}}$ | Derived from implementation | [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py), config_behavior_mapping | Tile packing constraint | PE count | System area and latency |

---

## 6. Module 6: Tile-, PE-, and System-Level Cost Estimation

### 6.1 Area Model

The simulator estimates total area as the sum of the per-layer hardware footprint:

$$
A_{\mathrm{total}} = \sum_{l} N_{\mathrm{tile}}(l)\,A_{\mathrm{tile}}(l) + A_{\mathrm{global}},
$$

with

$$
A_{\mathrm{tile}} = A_{\mathrm{xbar}} + A_{\mathrm{ADC}} + A_{\mathrm{DAC}} + A_{\mathrm{digital}} + A_{\mathrm{buf}} + A_{\mathrm{pooling}}.
$$

The digital sub-area is modeled as

$$
A_{\mathrm{digital}} = A_{\mathrm{adder}} + A_{\mathrm{shiftreg}} + A_{\mathrm{iReg}} + A_{\mathrm{oReg}} + A_{\mathrm{demux}} + A_{\mathrm{mux}} + A_{\mathrm{joint}}.
$$

### 6.2 Power Model

The power model is similarly additive:

$$
P_{\mathrm{total}} = \sum_l N_{\mathrm{tile}}(l)\,P_{\mathrm{tile}}(l) + P_{\mathrm{global}}.
$$

The tile power is decomposed as

$$
P_{\mathrm{tile}} = P_{\mathrm{xbar}} + P_{\mathrm{ADC}} + P_{\mathrm{DAC}} + P_{\mathrm{digital}} + P_{\mathrm{buf}} + P_{\mathrm{pooling}}.
$$

### 6.3 Latency Model

The latency model is a composite of buffer, compute, and transfer delays. A simplified form is

$$
T_{\mathrm{layer}} = T_{\mathrm{buf}} + T_{\mathrm{compute}} + T_{\mathrm{digital}} + T_{\mathrm{merge}} + T_{\mathrm{transfer}}.
$$

The compute portion is further decomposed into DAC, crossbar, and ADC timing:

$$
T_{\mathrm{compute}} = T_{\mathrm{DAC}} + T_{\mathrm{xbar}} + T_{\mathrm{ADC}}.
$$

### 6.4 Energy Model

Energy is the product of power and latency,

$$
E_{\mathrm{layer}} = P_{\mathrm{layer}} T_{\mathrm{layer}}.
$$

Aggregated over layers,

$$
E_{\mathrm{total}} = \sum_l E_{\mathrm{layer}}(l) + E_{\mathrm{NoC}}.
$$

### 6.5 Accuracy Model

The simulator also evaluates the impact of device non-idealities through a reduced-order accuracy model. The main effects are:

- stochastic stuck-at-faults (SAF),
- resistance variation,
- load-resistance and wire-resistance perturbation.

The perturbed conductance is represented as

$$
G_{ij}^{\mathrm{real}} = \frac{1}{R_{ij}^{\mathrm{real}}},
$$

with

$$
R_{ij}^{\mathrm{real}} = R_{ij}^{\mathrm{nom}} + \Delta R_{ij}^{\mathrm{wire}} + \Delta R_{ij}^{\mathrm{var}}.
$$

The output voltage is then estimated by a weighted summation of the input voltages through the perturbed conductances, which is used to approximate the effect on classification accuracy.

### 6.6 Equation provenance and dependencies

| Equation | Type | Implemented in | Theoretical origin | Dependency chain | Used by |
|---|---|---|---|---|---|
| Area aggregation | Derived from implementation | [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py) and [MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py](MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py) | Additive hardware cost model | PE/tile allocation | System area |
| Latency aggregation | Derived from implementation | [MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py](MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py), pipe_result_update | Pipeline timing decomposition | Buffer, DAC, xbar, ADC, digital delay | System latency |
| Energy aggregation | Derived from implementation | [MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py](MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py) | $E = P\,T$ | Power + latency | System energy |

---

## 7. Symbol Table

| Symbol | Meaning | Units |
|---|---|---|
| $U$ | Crossbar utilization | dimensionless |
| $R$ | Number of rows | dimensionless |
| $C$ | Number of columns | dimensionless |
| $N_r^{\mathrm{used}}$ | Number of active rows | dimensionless |
| $N_c^{\mathrm{used}}$ | Number of active columns | dimensionless |
| $G_{ij}$ | Cell conductance | Siemens |
| $R_{ij}$ | Cell resistance | $\Omega$ |
| $v_i$ | Input voltage | V |
| $P_{\mathrm{read}}$ | Read power | W |
| $P_{\mathrm{write}}$ | Write power | W |
| $A_{\mathrm{xbar}}$ | Crossbar area | $\mu m^2$ |
| $T_{\mathrm{wire}}$ | Wire delay | ns |
| $T_{\mathrm{read}}$ | Read latency | ns |
| $T_{\mathrm{write}}$ | Write latency | ns |
| $E_{\mathrm{read}}$ | Read energy | nJ |
| $E_{\mathrm{write}}$ | Write energy | nJ |

---

## 8. Complete Mathematical Pipeline

A compact end-to-end view of the simulator is:

1. Input tensor or image
2. Quantization and bit-slice decomposition
3. Weight mapping and crossbar partitioning
4. Conductance mapping using $G = 1/R$
5. Crossbar current and power using $P = V^2/R$
6. ADC/DAC scaling and partial-sum accumulation
7. PE and tile aggregation
8. Latency, power, area, and energy estimation
9. Accuracy degradation under non-ideal device behavior

At each stage, the implementation can be traced to the corresponding module in the codebase.

## 9. Equation-to-file map

| Equation family | Primary file(s) |
|---|---|
| Conductance and power | [MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py](MNSIM-2.0/MNSIM/Hardware_Model/Crossbar.py), [MNSIM-2.0/MNSIM/Hardware_Model/Device.py](MNSIM-2.0/MNSIM/Hardware_Model/Device.py) |
| Quantization and bit slicing | [MNSIM-2.0/MNSIM/Interface/quantize.py](MNSIM-2.0/MNSIM/Interface/quantize.py) |
| Mapping and PE/tile allocation | [MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py](MNSIM-2.0/MNSIM/Mapping_Model/Behavior_mapping.py) |
| Latency, power, energy aggregation | [MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py](MNSIM-2.0/MNSIM/Latency_Model/Model_latency.py) |

## 10. Master Equation Index (continuous)

1. $U = \dfrac{N_r^{\mathrm{used}} N_c^{\mathrm{used}}}{R C}$
2. $G_{ij} = \dfrac{1}{R_{ij}}$
3. $P_{\mathrm{read}} = \sum_{i=1}^{R}\sum_{j=1}^{C} G_{ij} v_i^2$
4. $P_{\mathrm{write}} = \dfrac{1}{N_r^{\mathrm{write}}} \sum_{i=1}^{N_r^{\mathrm{write}}}\sum_{j=1}^{N_c^{\mathrm{write}}} G_{ij}^{w} (v_i^{w})^2$
5. $P = \dfrac{V^2}{R}$
6. $A_{\mathrm{xbar}} = A_{\mathrm{cell}}RC + A_{\mathrm{driver}}R$
7. $A_{\mathrm{xbar}} = A_{\mathrm{cell}}RC + R(7.3\cdot2.7 + 9.5\cdot3.8)(T_{\mathrm{tr}}/65)^2$
8. $A_{\mathrm{xbar}} = 5RC$
9. $A_{\mathrm{xbar}} = 4RC T_{\mathrm{tech}}^2\times10^{-6}$
10. $A_{\mathrm{xbar}} = 3(W/L+1)RC T_{\mathrm{tech}}^2\times10^{-6}$
11. $S = \dfrac{RC}{1024\cdot8}$
12. $T_{\mathrm{wire}} = 10^{-3}(2\times10^{-4}S^2 + 5\times10^{-6}S + 4\times10^{-14})$
13. $T_{\mathrm{read}} = T_{\mathrm{dev,read}} + T_{\mathrm{wire}}$
14. $T_{\mathrm{write}} = T_{\mathrm{dev,write}} N_r^{\mathrm{write}}$
15. $E_{\mathrm{read}} = P_{\mathrm{read}}T_{\mathrm{read}}$
16. $E_{\mathrm{write}} = P_{\mathrm{write}}T_{\mathrm{write}}$
17. $\mathcal{R} = \{R_0, R_1, \dots, R_{L-1}\}$
18. $\eta = \dfrac{\Delta R}{R}$
19. $R_{\mathrm{eff}}^{(r)} = \dfrac{R_0 R_1}{0.67 R_1 + 0.33 R_0}$
20. $V_{\mathrm{read}} = \sqrt{0.9 V_{\mathrm{read},0}^2 + 0.1 V_{\mathrm{read},1}^2}$
21. $P_{\mathrm{read}}^{\mathrm{dev}} = \dfrac{V_{\mathrm{read}}^2}{R_{\mathrm{eff}}^{(r)}}$
22. $R_{\mathrm{eff}}^{(w)} = \sqrt{R_0 R_1}$
23. $V_{\mathrm{write}} = \dfrac{V_{\mathrm{write},0} + V_{\mathrm{write},1}}{2}$
24. $P_{\mathrm{write}}^{\mathrm{dev}} = \dfrac{V_{\mathrm{write}}^2}{R_{\mathrm{eff}}^{(w)}}$
25. $q(x;b,s) = \mathrm{clip}(\mathrm{round}(x/s \, \theta_b), -\theta_b, \theta_b) s/\theta_b$
26. $\theta_b = 2^{b-1}-1$
27. $s_a^{(t)} = \rho s_a^{(t-1)} + (1-\rho)(3\sigma_a^{(t)} + |\mu_a^{(t)}|)$
28. $y \approx \sum_{p,q}(x_p \otimes w_q)2^{p+q}$
29. $y_{\mathrm{ADC}} = \mathrm{round}(y \cdot 2^{\tau})$
30. $C_{\mathrm{xbar}} = \left\lfloor \dfrac{\text{xbar\_size}}{k^2} \right\rfloor$
31. $\Delta b_{\mathrm{ADC}} = \max(\lceil \log_2(C_{\mathrm{xbar}}k^2/\text{DAC\_num}) \rceil, 0)$
32. $N_{\mathrm{op}} = 2 \, S_{\mathrm{slide}} \, L_{\mathrm{kernel}} \, C_{\mathrm{out}}$
33. $N_{\mathrm{PE}} = \left\lceil \dfrac{C_{\mathrm{in}}}{C_{\mathrm{in,xbar}}} \right\rceil \left\lceil \dfrac{C_{\mathrm{out}}}{C_{\mathrm{out,xbar}}} \right\rceil \left\lceil \dfrac{b_w^{\mathrm{eff}}}{b_{\mathrm{PE}}} \right\rceil$
34. $N_{\mathrm{tile}} = \left\lceil \dfrac{N_{\mathrm{PE}}}{N_{\mathrm{PE}}^{\mathrm{tile}}} \right\rceil$
35. $A_{\mathrm{total}} = \sum_l N_{\mathrm{tile}}(l)A_{\mathrm{tile}}(l) + A_{\mathrm{global}}$
36. $P_{\mathrm{total}} = \sum_l N_{\mathrm{tile}}(l)P_{\mathrm{tile}}(l) + P_{\mathrm{global}}$
37. $T_{\mathrm{layer}} = T_{\mathrm{buf}} + T_{\mathrm{compute}} + T_{\mathrm{digital}} + T_{\mathrm{merge}} + T_{\mathrm{transfer}}$
38. $E_{\mathrm{layer}} = P_{\mathrm{layer}} T_{\mathrm{layer}}$
39. $E_{\mathrm{total}} = \sum_l E_{\mathrm{layer}}(l) + E_{\mathrm{NoC}}$
40. $G_{ij}^{\mathrm{real}} = 1/R_{ij}^{\mathrm{real}}$
41. $R_{ij}^{\mathrm{real}} = R_{ij}^{\mathrm{nom}} + \Delta R_{ij}^{\mathrm{wire}} + \Delta R_{ij}^{\mathrm{var}}$

---

## 11. Next Step

The next step is to continue expanding the same traceability structure for the remaining modules in the simulator, especially the ADC/DAC, PE, Tile, Power, and Accuracy stacks.