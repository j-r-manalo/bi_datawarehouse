import os


def combine_sql_files(directory, output_file):
    # Get a list of .sql files, sorted by the first two digits of their filenames
    sql_files = [f for f in os.listdir(directory) if f.endswith('.sql') and os.path.isfile(os.path.join(directory, f))]
    sql_files.sort(key=lambda x: x[:2])  # Sort based on the first two digits of the filename

    # Open the output file in write mode
    with open(output_file, 'w') as outfile:
        for filename in sql_files:
            file_path = os.path.join(directory, filename)
            print(f"Processing file: {file_path}")

            # Open each .sql file and write its contents to the output file
            with open(file_path, 'r') as infile:
                outfile.write(f'-- Content from {filename}\n')
                outfile.write(infile.read())
                outfile.write('\n\n')  # Separate the contents of each file

    print(f"All SQL files have been combined into {output_file}")


# Get the current directory of the script
input_directory = os.path.dirname(os.path.realpath(__file__))

# Final combined output file in the same directory as the script
output_file = os.path.join(input_directory, 'combined.sql')

# Combine the .sql files
combine_sql_files(input_directory, output_file)
