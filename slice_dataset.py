import csv
import random


def create_sample_dataset(input_file: str, output_file: str, sample_size: int) -> None:
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)
        print("Reading all songs into memory...")
        all_songs = list(reader)

    print(f"Total songs found: {len(all_songs)}. Sampling {sample_size}...")
    sampled_songs = random.sample(all_songs, sample_size)

    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow((header[1], header[2], *header[4:]))
        processed_rows = []
        for row in sampled_songs:
            new_row = [row[1], row[2]] + row[4:]
            processed_rows.append(new_row)

        writer.writerows(processed_rows)
    print(f"Success! New dataset saved as {output_file}.")


if __name__ == '__main__':
    size = 19000
    create_sample_dataset('spotify_data.csv', f'spotify_{size//1000}k.csv', size)
