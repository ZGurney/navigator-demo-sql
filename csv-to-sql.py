# import pandas as pd
# import sqlite3

# # Read the CSV file
# df = pd.read_csv('data/business.retailsales.csv')

# # Create a connection to the SQLite database
# conn = sqlite3.connect('data/business.db')

# # Write the DataFrame to a table in the database
# df.to_sql('table_name', conn, if_exists='replace', index=False)

# # Close the database connection
# conn.close()

import pandas as pd
import sqlite3

# Read the XLSX file
df = pd.read_excel('data/classified-patents.xlsx')

# Create a connection to the SQLite database
conn = sqlite3.connect('data/classified-patents.db')

# Write the DataFrame to a table in the database
df.to_sql('table_name', conn, if_exists='replace', index=False)

# Close the database connection
conn.close()