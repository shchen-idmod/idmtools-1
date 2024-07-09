import h5py
import pandas as pd

# Open your HDF5 file
file_path = 'data_compressed.hdf5'
with h5py.File(file_path, 'r') as file:
    # Assume that you know the dataset you are interested in is called 'data'
    # You can list all keys by list(file.keys()) if you are unsure
    data = file['data'][:]  # This slices all data from the dataset
# Convert the numpy array to a pandas DataFrame
# Assuming 'data' is a structured array or a simple numpy array
df = pd.DataFrame(data)
