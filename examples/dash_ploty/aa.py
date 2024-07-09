import pandas as pd

# Sample DataFrame
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
}, index=['first', 'second', 'third'])

# Update the value in column 'B' where the index label is 'second'
df.at['second', 'B'] = 55

print(df)
