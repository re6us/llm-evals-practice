import csv


with open ("posts.csv", "r", encoding="utf-8") as f_in, \
    open("golden.csv", "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["title", "true_topic"])

        for row in reader:

            writer.writerow([row["title"], ""])