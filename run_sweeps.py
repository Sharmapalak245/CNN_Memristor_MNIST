import os
import sys
import copy
import math
import shutil
import collections
import re
import numpy as np
import torch
import matplotlib.pyplot as plt
import configparser

# Setup paths
PROJECT_ROOT = os.path.abspath("./MNSIM-2.0")
sys.path.append(PROJECT_ROOT)

from MNSIM.Interface.interface import TrainTestInterface
from MNSIM.Accuracy_Model.Weight_update import weight_update
from MNSIM.Mapping_Model.Tile_connection_graph import TCG
from MNSIM.Latency_Model.Model_latency import Model_latency
from MNSIM.Area_Model.Model_Area import Model_area
from MNSIM.Power_Model.Model_inference_power import Model_inference_power
from MNSIM.Energy_Model.Model_energy import Model_energy

CONFIG_PATH = os.path.join(PROJECT_ROOT, "SimConfig.ini")
BACKUP_PATH = os.path.join(PROJECT_ROOT, "SimConfig.ini.bak")

def backup_config():
    if os.path.exists(CONFIG_PATH):
        shutil.copyfile(CONFIG_PATH, BACKUP_PATH)

def restore_config():
    if os.path.exists(BACKUP_PATH):
        shutil.copyfile(BACKUP_PATH, CONFIG_PATH)
        os.remove(BACKUP_PATH)

def modify_config(modifications):
    # Modifications is a dict of {section: {param: value}}
    # Read backup config to modify to preserve comments/structure
    with open(BACKUP_PATH, 'r') as f:
        content = f.read()
    
    for section, params in modifications.items():
        # Find section block
        for param, val in params.items():
            # Replace param line within section
            # We construct a regex to match the parameter line after the section header
            pattern = rf"(?<=^\[{section}\])(.*?)(^\s*{param}\s*=.*?$)"
            # Better regex replacement using configparser or basic regex:
            # Let's parse and reconstruct dynamically to ensure we don't break the format
    
    # We will use configparser for simplicity since comments are preserved in the backup
    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(BACKUP_PATH, encoding='UTF-8')
    for section, params in modifications.items():
        for param, val in params.items():
            config.set(section, param, str(val))
    with open(CONFIG_PATH, 'w', encoding='UTF-8') as f:
        config.write(f)

def run_simulation_metrics():
    # Helper to load structure and run area, latency, power, energy estimation
    interface = TrainTestInterface(
        network_module='lenet',
        dataset_module='MNSIM.Interface.mnist',
        SimConfig_path=CONFIG_PATH,
        weights_file=os.path.join(PROJECT_ROOT, 'MNSIM', 'Interface', 'zoo', 'mnist_lenet_99qbitpim_params.pth'),
        device=0
    )
    struct = interface.get_structure()
    tcg = TCG(struct, CONFIG_PATH)
    
    # Latency
    latency = Model_latency(NetStruct=struct, SimConfig_path=CONFIG_PATH, TCG_mapping=tcg)
    latency.calculate_model_latency(mode=1)
    tot_latency = max(max(latency.finish_time)) # ns
    
    # Area
    area = Model_area(NetStruct=struct, SimConfig_path=CONFIG_PATH, TCG_mapping=tcg)
    tot_area = area.arch_total_area # um^2
    
    # Power
    power = Model_inference_power(NetStruct=struct, SimConfig_path=CONFIG_PATH, TCG_mapping=tcg)
    tot_power = power.arch_total_power # W
    
    # Energy
    energy = Model_energy(NetStruct=struct, SimConfig_path=CONFIG_PATH, model_latency=latency, model_power=power, TCG_mapping=tcg)
    tot_energy = energy.arch_total_energy # nJ
    
    # Accuracy
    weight = interface.get_net_bits()
    # Disable SAF & Variation for clean baseline unless we are sweeping variation
    # Reading config to see if variation should be enabled
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    var_val = float(config.get('Device level', 'Device_Variation'))
    is_var = (var_val > 0)
    
    weight_2 = weight_update(CONFIG_PATH, weight, is_Variation=is_var, is_SAF=True, is_Rratio=False)
    acc = interface.set_net_bits_evaluate(weight_2, adc_action='SCALE')
    
    return {
        'accuracy': acc,
        'latency': tot_latency,
        'area': tot_area,
        'power': tot_power,
        'energy': tot_energy,
        'layer_energy': [energy.arch_energy[i] for i in range(len(struct))],
        'layer_area': [area.arch_area[i] for i in range(len(struct))]
    }

def main():
    print("Backing up config file...")
    backup_config()
    
    try:
        # ==========================================
        # SWEEP 1: ADC Precision (4, 6, 8, 10 bits)
        # ==========================================
        print("\n--- Sweeping ADC Precision ---")
        adc_bits = [4, 6, 8, 10]
        adc_results = []
        for bits in adc_bits:
            print(f"Running simulation for ADC Precision = {bits} bits...")
            modify_config({
                'Interface level': {'ADC_Precision': bits},
                'Device level': {'Device_Variation': 0.0, 'Device_SAF': '0.0,0.0'}
            })
            metrics = run_simulation_metrics()
            adc_results.append(metrics)
            print(f"Result: Acc = {metrics['accuracy']:.4f}, Latency = {metrics['latency']:.2f} ns, Energy = {metrics['energy']:.2f} nJ, Area = {metrics['area']:.2f} um^2")
        
        # ==========================================
        # SWEEP 2: DAC Precision (4, 6, 8 bits)
        # ==========================================
        print("\n--- Sweeping DAC Precision ---")
        dac_bits = [4, 6, 8]
        dac_results = []
        for bits in dac_bits:
            print(f"Running simulation for DAC Precision = {bits} bits...")
            modify_config({
                'Interface level': {'DAC_Precision': bits, 'ADC_Precision': 6},
                'Device level': {'Device_Variation': 0.0, 'Device_SAF': '0.0,0.0'}
            })
            metrics = run_simulation_metrics()
            dac_results.append(metrics)
            print(f"Result: Acc = {metrics['accuracy']:.4f}")
            
        # ==========================================
        # SWEEP 3: Device Variation (0%, 2%, 5%, 8.8%, 12%, 15%, 20%)
        # ==========================================
        print("\n--- Sweeping Device Variation ---")
        variations = [0.0, 2.0, 5.0, 8.8, 12.0, 15.0, 20.0]
        var_results = []
        for var in variations:
            print(f"Running simulation for Device Variation = {var}%...")
            modify_config({
                'Device level': {'Device_Variation': var, 'Device_SAF': '0.0,0.0'},
                'Interface level': {'ADC_Precision': 6, 'DAC_Precision': 8}
            })
            metrics = run_simulation_metrics()
            var_results.append(metrics)
            print(f"Result: Acc = {metrics['accuracy']:.4f}")

        # ==========================================
        # SWEEP 4: Crossbar Size (128x128 vs 256x256)
        # ==========================================
        print("\n--- Sweeping Crossbar Size ---")
        xbar_sizes = [128, 256]
        xbar_results = []
        for size in xbar_sizes:
            print(f"Running simulation for Crossbar Size = {size}x{size}...")
            modify_config({
                'Crossbar level': {'Xbar_Size': f"{size},{size}", 'Subarray_Size': size},
                'Process element level': {'DAC_Num': size // 2, 'ADC_Num': size // 2}, # keep DAC_Num / ADC_Num multiplexing constant
                'Device level': {'Device_Variation': 0.0, 'Device_SAF': '0.0,0.0'},
                'Interface level': {'ADC_Precision': 6, 'DAC_Precision': 8}
            })
            metrics = run_simulation_metrics()
            xbar_results.append(metrics)
            print(f"Result: Acc = {metrics['accuracy']:.4f}, Area = {metrics['area']:.2f} um^2, Latency = {metrics['latency']:.2f} ns, Energy = {metrics['energy']:.2f} nJ")

        # Restore configuration to original before plotting
        print("\nRestoring config file...")
        restore_config()

        # ==========================================
        # PLOTTING AND GRAPH GENERATION
        # ==========================================
        print("\nGenerating Graph Files...")
        os.makedirs("./graphs", exist_ok=True)

        # Helper to plot styling
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        plt.rcParams.update({'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 13})

        # 01_device_iv_characteristics.png
        # Derived: I = V / R. LRS = 10k, HRS = 1M. V in [-1, 1]
        v_sweep = np.linspace(-1.0, 1.0, 100)
        i_lrs = v_sweep / 1e4 * 1e6 # in uA
        i_hrs = v_sweep / 1e6 * 1e6 # in uA
        plt.figure(figsize=(6, 4))
        plt.plot(v_sweep, i_lrs, label="LRS (10 k$\Omega$)", color='#1f77b4', linewidth=2)
        plt.plot(v_sweep, i_hrs, label="HRS (1 M$\Omega$)", color='#ff7f0e', linewidth=2)
        plt.xlabel("Applied Voltage (V)")
        plt.ylabel("Current ($\mu$A)")
        plt.title("Device-Level I–V Characteristics (Ohmic Model)")
        plt.legend()
        plt.tight_layout()
        plt.savefig("01_device_iv_characteristics.png", dpi=300)
        plt.close()

        # 02_device_conductance_states.png
        # Derived: G = 1/R (linear region V in [0, 0.15])
        v_read = np.linspace(0.0, 0.15, 50)
        g_lrs = np.ones_like(v_read) / 1e4 * 1e6 # uS
        g_hrs = np.ones_like(v_read) / 1e6 * 1e6 # uS
        plt.figure(figsize=(6, 4))
        plt.plot(v_read, g_lrs, label="LRS Conductance ($100\,\mu$S)", color='#1f77b4', linewidth=2)
        plt.plot(v_read, g_hrs, label="HRS Conductance ($1\,\mu$S)", color='#ff7f0e', linewidth=2)
        plt.xlabel("Read Voltage (V)")
        plt.ylabel("Conductance ($\mu$S)")
        plt.title("Device Conductance States in Linear Sweep Region")
        plt.ylim(-5, 110)
        plt.legend()
        plt.tight_layout()
        plt.savefig("02_device_conductance_states.png", dpi=300)
        plt.close()

        # 03_weight_conductance_distribution.png
        # Actual weights from pretrained LeNet
        weights_dict = torch.load(os.path.join(PROJECT_ROOT, 'MNSIM', 'Interface', 'zoo', 'mnist_lenet_99qbitpim_params.pth'), map_location='cpu')
        flat_weights = []
        for k, v in weights_dict.items():
            if 'weight' in k:
                flat_weights.extend(v.numpy().flatten())
        flat_weights = np.array(flat_weights)
        
        plt.figure(figsize=(6, 4))
        plt.hist(flat_weights, bins=50, color='#2ca02c', edgecolor='black', alpha=0.7)
        plt.xlabel("Weight Value")
        plt.ylabel("Frequency")
        plt.title("Pretrained LeNet Weight Distribution")
        plt.tight_layout()
        plt.savefig("03_weight_conductance_distribution.png", dpi=300)
        plt.close()
        
        # Calculate stats for Graph 3
        print(f"Weight Stats: Min = {flat_weights.min():.4f}, Max = {flat_weights.max():.4f}, Mean = {flat_weights.mean():.4f}, Std = {flat_weights.std():.4f}, Count = {len(flat_weights)}")

        # 04_input_voltage_crossbar_current.png
        # Derived/Implemented MVM: I_j = sum(V_i * G_ij).
        # We can plot output current vs input voltage step for a single column with LRS cells.
        input_levels = np.arange(256)
        v_in = input_levels * 0.15 / 255.0
        # For a single column of 256 rows mapped to LRS:
        current_lrs = 256 * v_in / 1e4 * 1e3 # mA
        current_hrs = 256 * v_in / 1e6 * 1e3 # mA
        plt.figure(figsize=(6, 4))
        plt.plot(input_levels, current_lrs, label="All-LRS Column (Current max ~3.84 mA)", color='#1f77b4', linewidth=2)
        plt.plot(input_levels, current_hrs, label="All-HRS Column (Current max ~0.0384 mA)", color='#ff7f0e', linewidth=2)
        plt.xlabel("Input Activation Level (0-255)")
        plt.ylabel("Column Accumulation Current (mA)")
        plt.title("Ideal MVM Column Current vs Input Activation Level")
        plt.legend()
        plt.tight_layout()
        plt.savefig("04_input_voltage_crossbar_current.png", dpi=300)
        plt.close()

        # 05_ideal_vs_nonideal_mvm.png
        # Plotted: Current distribution with 8.8% device variation on an MVM column current.
        # Assuming a target sum of 128 LRS cells and 128 HRS cells, with variation.
        # G_real = 1 / (R + delta_R)
        np.random.seed(42)
        ideal_g_sum = 128 * (1/1e4) + 128 * (1/1e6) # Siemens
        ideal_current = ideal_g_sum * 0.04743 # effective read voltage ~0.04743 V
        
        # Simulating 10,000 non-ideal column current samples
        non_ideal_currents = []
        for _ in range(10000):
            r_lrs_var = np.random.normal(loc=1e4, scale=1e4 * 0.088, size=128)
            r_hrs_var = np.random.normal(loc=1e6, scale=1e6 * 0.088, size=128)
            g_sum_var = np.sum(1.0 / r_lrs_var) + np.sum(1.0 / r_hrs_var)
            non_ideal_currents.append(g_sum_var * 0.04743)
        non_ideal_currents = np.array(non_ideal_currents) * 1e6 # in uA
        ideal_current_ua = ideal_current * 1e6
        
        plt.figure(figsize=(6, 4))
        plt.hist(non_ideal_currents, bins=50, color='#9467bd', edgecolor='black', alpha=0.7, label='Variation-Affected')
        plt.axvline(ideal_current_ua, color='red', linestyle='--', linewidth=2, label=f'Ideal ({ideal_current_ua:.2f} $\mu$A)')
        plt.xlabel("Column Current ($\mu$A)")
        plt.ylabel("Frequency")
        plt.title("Ideal vs Device-Variation-Affected Crossbar Current")
        plt.legend()
        plt.tight_layout()
        plt.savefig("05_ideal_vs_nonideal_mvm.png", dpi=300)
        plt.close()

        # 08_accuracy_vs_device_variation.png
        # Experimentally Simulated: Variation vs Accuracy
        plt.figure(figsize=(6, 4))
        acc_vals = [r['accuracy'] * 100 for r in var_results]
        plt.plot(variations, acc_vals, marker='o', color='#d62728', linewidth=2)
        plt.xlabel("Device Variation (%)")
        plt.ylabel("Inference Accuracy (%)")
        plt.title("Inference Accuracy vs Device Variation")
        plt.ylim(0, 105)
        plt.tight_layout()
        plt.savefig("08_accuracy_vs_device_variation.png", dpi=300)
        plt.close()

        # 10_accuracy_vs_adc_precision.png
        # Experimentally Simulated: ADC bits vs Accuracy, Latency, Energy, Area
        fig, ax1 = plt.subplots(figsize=(6, 4))
        accs = [r['accuracy'] * 100 for r in adc_results]
        ax1.plot(adc_bits, accs, marker='s', color='#1f77b4', linewidth=2, label="Accuracy")
        ax1.set_xlabel("ADC Precision (bits)")
        ax1.set_ylabel("Inference Accuracy (%)", color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.set_ylim(0, 105)
        
        ax2 = ax1.twinx()
        energies = [r['energy'] for r in adc_results]
        ax2.plot(adc_bits, energies, marker='^', color='#ff7f0e', linewidth=2, linestyle='--', label="Energy")
        ax2.set_ylabel("Energy Consumption (nJ)", color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        
        plt.title("Inference Accuracy & Energy vs ADC Precision")
        fig.tight_layout()
        plt.savefig("10_accuracy_vs_adc_precision.png", dpi=300)
        plt.close()

        # 11_accuracy_vs_dac_precision.png
        # Experimentally Simulated: DAC bits vs Accuracy
        plt.figure(figsize=(6, 4))
        dac_accs = [r['accuracy'] * 100 for r in dac_results]
        plt.plot(dac_bits, dac_accs, marker='d', color='#2ca02c', linewidth=2)
        plt.xlabel("DAC Precision (bits)")
        plt.ylabel("Inference Accuracy (%)")
        plt.title("Inference Accuracy vs DAC Precision")
        plt.ylim(0, 105)
        plt.tight_layout()
        plt.savefig("11_accuracy_vs_dac_precision.png", dpi=300)
        plt.close()

        # 12_accuracy_vs_crossbar_size.png
        # Experimentally Simulated: 128 vs 256
        xbar_labels = [f"{s}x{s}" for s in xbar_sizes]
        xbar_accs = [r['accuracy'] * 100 for r in xbar_results]
        xbar_areas = [r['area'] / 1e6 for r in xbar_results] # mm^2
        
        fig, ax1 = plt.subplots(figsize=(6, 4))
        width = 0.35
        x = np.arange(len(xbar_sizes))
        ax1.bar(x - width/2, xbar_accs, width, label='Accuracy', color='#1f77b4')
        ax1.set_ylabel("Inference Accuracy (%)", color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.set_xticks(x)
        ax1.set_xticklabels(xbar_labels)
        ax1.set_ylim(0, 105)
        
        ax2 = ax1.twinx()
        ax2.bar(x + width/2, xbar_areas, width, label='Area', color='#ff7f0e', alpha=0.8)
        ax2.set_ylabel("Total Area (mm$^2$)", color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        
        plt.title("Accuracy & Area for Different Crossbar Dimensions")
        fig.tight_layout()
        plt.savefig("12_accuracy_vs_crossbar_size.png", dpi=300)
        plt.close()

        # 13_energy_vs_layer.png
        # Experimentally Simulated: energy values per layer
        layers = ["Conv1", "Pool1", "Conv2", "Pool2", "Conv3", "FC1", "FC2"]
        # Use baseline (which has original config parameters) energy results
        # Baseline results can be found in the second run of adc_results (index 1 is 6-bit ADC, which is baseline)
        baseline_results = adc_results[1]
        plt.figure(figsize=(7, 4))
        plt.bar(layers, baseline_results['layer_energy'], color='#e377c2', edgecolor='black', alpha=0.8)
        plt.xlabel("LeNet Layer")
        plt.ylabel("Energy Consumption (nJ)")
        plt.title("Energy Consumption Profile Across Network Layers")
        plt.tight_layout()
        plt.savefig("13_energy_vs_layer.png", dpi=300)
        plt.close()

        # 14_area_vs_layer.png
        # Experimentally Simulated: area values per layer
        plt.figure(figsize=(7, 4))
        plt.bar(layers, [a / 1e6 for a in baseline_results['layer_area']], color='#bcbd22', edgecolor='black', alpha=0.8) # in mm^2
        plt.xlabel("LeNet Layer")
        plt.ylabel("Hardware Layout Area (mm$^2$)")
        plt.title("Layout Area Footprint Across Network Layers")
        plt.tight_layout()
        plt.savefig("14_area_vs_layer.png", dpi=300)
        plt.close()

        # 17_layerwise_crossbar_mapping.png
        # Visual diagram of weight mapping
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.axis('off')
        box_props = dict(boxstyle="round,pad=0.5", fc="#d6f5d6", ec="g", lw=2)
        arrow_props = dict(arrowstyle="->", lw=2, color="gray")
        
        ax.text(0.5, 0.9, "CNN Weight Tensor\n(e.g., [6, 3, 5, 5])", ha="center", va="center", bbox=box_props)
        ax.text(0.5, 0.65, "Flatten & Reshape\n(e.g., 75 rows, 6 columns)", ha="center", va="center", bbox=box_props)
        ax.text(0.5, 0.4, "Weight Bit-Slicing (8 slices)\n& Signed Splitting (Pos/Neg Arrays)", ha="center", va="center", bbox=box_props)
        ax.text(0.5, 0.15, "Differential 256x256 Crossbar Arrays\n(16 crossbars used for Layer 0)", ha="center", va="center", bbox=box_props)
        
        ax.annotate("", xy=(0.5, 0.75), xytext=(0.5, 0.82), arrowprops=arrow_props)
        ax.annotate("", xy=(0.5, 0.5), xytext=(0.5, 0.58), arrowprops=arrow_props)
        ax.annotate("", xy=(0.5, 0.25), xytext=(0.5, 0.32), arrowprops=arrow_props)
        
        plt.title("Layer-wise Mapping Strategy of Convolution Weights to Crossbars", pad=20)
        plt.tight_layout()
        plt.savefig("17_layerwise_crossbar_mapping.png", dpi=300)
        plt.close()

        print("\nAll graphs generated successfully!")
        
    except Exception as e:
        print(f"Error during sweeps or plotting: {e}")
        restore_config()
        raise e

if __name__ == '__main__':
    main()
