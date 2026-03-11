import matplotlib.pyplot as plt
import numpy as np

# Prompt user for the input file name
filename = input("Enter the input text file name: ")
filename_input = filename + '.txt'

# Read the data from the file
try:
    with open(filename_input, 'r') as file:
        lines = file.readlines()
except FileNotFoundError:
    print(f"File '{filename}' not found. Aborting.")
    sys.exit(1)

# Parse the numbers: strip whitespace, remove commas, convert to int, skip non-numeric lines
data = []
for line in lines:
    stripped = line.strip().replace(',', '')
    if stripped:
        try:
            data.append(int(stripped))
        except ValueError:
            pass  # Skip non-numeric lines
            

RMS_calc = input("Calculate RMS? y/n: ")
if RMS_calc == 'y':
    RMS_range = int(input("Use RMS range as\n1: number of samples\n2: period in ms\n"))
    if RMS_range == 1:
        # Prompt user for the number of samples per RMS calculation
        N = int(input("Enter the number of samples per RMS calculation: "))
    elif RMS_range == 2:
        time = int(input("Enter the time period in ms: "))
        sampling_rate = 3906
        N = round(sampling_rate * time/1000)
    # Check if total samples are smaller than N
    else:
        sys.exit(1)
    
    if len(data) < N:
        print("Number of samples is smaller than desired range, skipping RMS calculation.")
    else:
        # Calculate RMS for every N samples (non-overlapping full chunks)
        rms_list = []
        for i in range(0, len(data), N):
            chunk = data[i:i + N]
            if len(chunk) == N:
                rms = np.sqrt(np.mean(np.square(chunk)))
                rms_list.append(rms)

        # Save the RMS values to a comma-separated text file
        with open('rms_values.txt', 'w') as f:
            f.write('\n'.join(str(val) for val in rms_list))
        print("RMS values saved to 'rms_values.txt'")
elif RMS_calc == 'n':
    print("RMS not calculated")
else:
    sys.exit(1)
    
plot_ripple = int(input("Plot ripple data?\n1: display\n2:save as image\n3: both\n"))
    
if 0 < plot_ripple < 4:
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(data)
    plt.title('Waveform of Ripple Control')
    plt.xlabel('Sample Index')
    plt.ylabel('Value')
    plt.grid(True)

    # Ask if the user wants to save the image
    if plot_ripple == 2 or plot_ripple == 3:
        filename = input("Enter the file name to save the image (without extension): ")
        plt.savefig(f"{filename}.png")
        print(f"Plot saved as '{filename}.png'")

    # Display the plot
    if plot_ripple == 1 or plot_ripple == 3:
        plt.show()
else:
    sys.exit(1);

