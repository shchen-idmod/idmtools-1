import pandas as pd

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
}, index=['x', 'y', 'z'])

# Get the row with index 'y' as a DataFrame
row_df = df.loc['y':'y']
print(row_df)