import pandas as pd
import matplotlib.pyplot as plt

from add_exercise import init_gsheet


def plot_progress(exercise):
    sheet = init_gsheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Фильтрация по упражнению
    df = df[df["Упражнение"] == exercise]
    df["Дата"] = pd.to_datetime(df["Дата"])
    df.sort_values("Дата", inplace=True)

    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(df["Дата"], df["Вес (кг)"], marker="o")
    plt.title(f"Прогресс в {exercise}")
    plt.xlabel("Дата")
    plt.ylabel("Вес (кг)")
    plt.grid()
    plt.savefig(f"{exercise}_progress.png")  # или plt.show()