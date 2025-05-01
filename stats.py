import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from add_exercise import init_gsheet
from datetime import datetime, timedelta


class StatsStates:
    WAITING_FOR_PERIOD = "waiting_for_stats_period"


async def start_stats(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите период для статистики:\n"
        "1 - За последнюю неделю\n"
        "2 - За последний месяц\n"
        "3 - За все время\n"
        "Введите цифру (1-3):"
    )
    await state.set_state(StatsStates.WAITING_FOR_PERIOD)


async def process_stats_data(message: types.Message, state: FSMContext, bot: Bot):
    try:
        period_choice = message.text.strip()
        if period_choice not in ['1', '2', '3']:
            await message.answer("Пожалуйста, введите цифру от 1 до 3")
            return

        # Получаем данные из Google Sheets
        sheet = init_gsheet()
        records = sheet.get_all_values()

        # Создаем DataFrame - берем все строки кроме заголовка
        data = []
        for row in records[1:]:  # Пропускаем заголовок
            if len(row) >= 5:  # Нам нужно минимум 5 столбцов
                data.append({
                    'Дата': row[0],
                    'Упражнение': row[1],
                    'Подходы': row[2],
                    'Повторения': row[3],
                    'Вес (кг)': row[4]
                })

        df = pd.DataFrame(data)

        # Преобразуем типы данных
        try:
            df['Дата'] = pd.to_datetime(df['Дата'], format='%Y-%m-%d', errors='coerce')
            df['Подходы'] = pd.to_numeric(df['Подходы'], errors='coerce')
            df['Повторения'] = pd.to_numeric(df['Повторения'], errors='coerce')
            df['Вес (кг)'] = pd.to_numeric(df['Вес (кг)'], errors='coerce')

            # Удаляем только строки с некорректными датами или пустыми упражнениями
            df = df.dropna(subset=['Дата', 'Упражнение'])

            # Фильтруем только неположительные значения подходов и повторений
            df = df[(df['Подходы'] > 0) & (df['Повторения'] > 0)]

            # Не фильтруем по весу, чтобы включить все записи
            # df = df[(df['Вес (кг)'] >= 0) & (df['Вес (кг)'] < 1000)]

        except Exception as e:
            await message.answer("Ошибка при обработке данных таблицы")
            print(f"Ошибка преобразования данных: {str(e)}")
            await state.clear()
            return

        if df.empty:
            await message.answer("Нет корректных данных для анализа")
            await state.clear()
            return

        # Фильтруем по периоду
        today = datetime.now()
        if period_choice == '1':
            start_date = today - timedelta(days=7)
            df = df[df['Дата'] >= start_date]
            period_title = "за последнюю неделю"
        elif period_choice == '2':
            start_date = today - timedelta(days=30)
            df = df[df['Дата'] >= start_date]
            period_title = "за последний месяц"
        else:
            period_title = "за все время"

        if df.empty:
            await message.answer(f"Нет данных для отображения {period_title}")
            await state.clear()
            return

        # Рассчитываем статистику
        # Количество уникальных тренировочных дней
        unique_days = df['Дата'].dt.date.nunique()

        # Общее количество подходов и повторений
        total_sets = int(df['Подходы'].sum())
        total_reps = int((df['Подходы'] * df['Повторения']).sum())

        # Самое популярное упражнение (по количеству записей)
        most_common_exercise_by_entries = df['Упражнение'].value_counts().idxmax()

        # Упражнение с максимальным количеством повторений
        df['Общие_повторения'] = df['Подходы'] * df['Повторения']
        exercise_by_reps = df.groupby('Упражнение')['Общие_повторения'].sum().idxmax()

        # Упражнение с максимальным количеством подходов
        exercise_by_sets = df.groupby('Упражнение')['Подходы'].sum().idxmax()

        # Самый активный день
        most_active_day = df['Дата'].dt.date.value_counts().idxmax().strftime('%d.%m.%Y')

        # Количество уникальных упражнений и общее количество записей
        unique_exercises = df['Упражнение'].nunique()
        total_exercise_entries = len(df)

        # Создаем графики
        img_buffer = BytesIO()
        plt.figure(figsize=(12, 16))

        # 1. Количество подходов по упражнениям
        plt.subplot(3, 1, 1)
        df.groupby('Упражнение')['Подходы'].sum().sort_values().plot(kind='barh', color='skyblue')
        plt.title('Общее количество подходов')
        plt.xlabel('Подходы')
        plt.grid(axis='x')

        # 2. Количество повторений по упражнениям
        plt.subplot(3, 1, 2)
        df.groupby('Упражнение')['Общие_повторения'].sum().sort_values().plot(kind='barh', color='lightgreen')
        plt.title('Общее количество повторений')
        plt.xlabel('Повторения')
        plt.grid(axis='x')

        # 3. Активность по дням
        plt.subplot(3, 1, 3)
        df['Дата'].dt.date.value_counts().sort_index().plot(kind='bar', color='salmon')
        plt.title('Активность по дням')
        plt.ylabel('Количество записей')
        plt.xticks(rotation=45)
        plt.grid(axis='y')

        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=80)
        plt.close()

        # Формируем текстовую статистику
        stats_text = (
            f"📊 Статистика {period_title}:\n"
            f"• Всего записей упражнений: {total_exercise_entries}\n"
            f"• Уникальных упражнений: {unique_exercises}\n"
            f"• Тренировочных дней: {unique_days}\n"
            f"• Всего подходов: {total_sets}\n"
            f"• Всего повторений: {total_reps}\n"
            f"• Самое частое упражнение: {most_common_exercise_by_entries}\n"
            f"• Упражнение с макс. подходами: {exercise_by_sets}\n"
            f"• Упражнение с макс. повторениями: {exercise_by_reps}\n"
            f"• Самый активный день: {most_active_day}\n"
            f"• Период: {df['Дата'].min().strftime('%d.%m.%Y')} - {df['Дата'].max().strftime('%d.%m.%Y')}"
        )

        # Отправляем результат
        img_buffer.seek(0)
        await message.answer_photo(
            BufferedInputFile(img_buffer.read(), filename="stats.png"),
            caption=stats_text
        )

    except Exception as e:
        await message.answer("Произошла ошибка при формировании отчета")
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await state.clear()