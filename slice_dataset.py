"""
CSC111 Winter 2026 Course Project: MatchMyMusic (Data Slicer)

Module Description
==================
This module contains a utility script used to preprocess the raw Spotify dataset.
It randomly samples a specified number of songs from the original dataset and
removes unnecessary columns to reduce file size and optimize graph generation.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the
authors listed below. All forms of distribution of this code, whether
as given or with any changes, are expressly prohibited.

This file is Copyright (c) 2026 Reuben Kurian Mathew, Arjun Nilesh Alwe, Ritvik Aggarwal
"""

import csv
import random


def create_sample_dataset(input_file: str, output_file: str, sample_size: int) -> None:
    """Read a large Spotify CSV dataset, extract a random sample of rows,
    remove unnecessary columns, and write the cleaned data to a new CSV file.

    Preconditions:
        - sample_size > 0
        - input_file is a valid path to a CSV file with at least sample_size rows
    """
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)
        print("Reading songs...")
        all_songs = list(reader)

    print(f"Total songs: {len(all_songs)}. Sampling {sample_size} songs...")
    sampled_songs = random.sample(all_songs, sample_size)

    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)

        writer.writerow((header[1], header[2], *header[4:]))

        processed_rows = []
        for row in sampled_songs:
            new_row = [row[1], row[2]] + row[4:]
            processed_rows.append(new_row)

        writer.writerows(processed_rows)

    print(f"Successfully generated {output_file}")


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['csv', 'random'],
        'allowed-io': ['create_sample_dataset'],
        'max-line-length': 120
    })
