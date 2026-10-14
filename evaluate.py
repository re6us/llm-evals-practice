import csv

golden = {}
with open ("golden.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        golden[row["title"]] = row["true_topic"]

total = 0
correct = 0

with open("posts_classified.csv", "r", encoding="utf-8") as f, \
    open("errors.csv", "w", newline="", encoding="utf-8") as f_err:
    err_writer = csv.writer(f_err)
    err_writer.writerow(["title", "model", "mine"])
    for row in csv.DictReader(f):
        model_topic = row["topic"].strip().lower()
        true_topic = golden[row["title"]].strip().lower()
        if model_topic == true_topic:
            correct += 1
        else:
            err_writer.writerow([row["title"], model_topic, true_topic])
            print(f"{row['title']}")
            print(f"    модель: {model_topic} | я: {true_topic}")
        total +=1

print(f"Точность: {correct / total * 100:.1f}%")