import os
import pandas as pd
import numpy as np
import originpro as op

# 1. Apni .opju file ka sahi path yahan dalo (agar file same folder mein hai toh bas naam dalo)
opju_filename = "MoS2 Kaust.opju" 

print("OriginPro se file open ho rahi hai...")

# Background mein Origin ko hidden mode mein kholo
op.set_show(False) 
op.open(file=os.path.abspath(opju_filename), readonly=True)

# First worksheet se data extract karo
wks = op.find_sheet('w')
v_data = wks.to_list(0) # Voltage Column
i_data = wks.to_list(1) # Conductance/Current Column

# Origin ko safely close karo
op.exit()

# 2. Data ko Pandas DataFrame mein daalo
df = pd.DataFrame({"Voltage": v_data, "Conductance": i_data})
df["Resistance"] = 1.0 / df["Conductance"]

# CSV format mein auto-save kar lo
df.to_csv("device_iv_data.csv", index=False)
print("Data extract ho kar 'device_iv_data.csv' save ho gaya hai!")

# 3. Read Voltage 0.2V par LRS aur HRS calculate karo
v_target = 0.2
read_points = df[np.isclose(df["Voltage"].abs(), v_target, atol=0.02)]

r_lrs = read_points["Resistance"].min()
r_hrs = read_points["Resistance"].max()

print("\n" + "="*40)
print(f"Extracted R_LRS : {r_lrs:.2f} Ohms")
print(f"Extracted R_HRS : {r_hrs:.2f} Ohms")
print(f"ON/OFF Ratio    : {(r_hrs/r_lrs):.2f}x")
print("="*40)

# 4. Automatically MNSIM ki SimConfig.ini file bana do
config_content = f"""[Device level]
Device_Tech = 65
Device_Bit_Level = 1
R_LRS = {r_lrs:.1f}
R_HRS = {r_hrs:.1f}
V_read = 0.2
V_write = 0.8
Device_Variation = 0
Device_SAF = 0,0

[Crossbar level]
Cell_Num_Row = 128
Cell_Num_Column = 128
Wire_Resistance = 10
Load_Resistance = 2e8

[ADC DAC level]
DAC_Choice = 1
DAC_Precision = 8
ADC_Choice = 1
ADC_Precision = 6

[Algorithm Configuration]
Net_Name = LeNet
Quantization_Bit = 8
"""

with open("SimConfig.ini", "w") as f:
    f.write(config_content)

print("\nSimConfig.ini file successfully MNSIM ke liye ready ho gayi hai!")