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

        # Для отладки выведем структуру данных
        print("Полученные данные:")
        for i, row in enumerate(records[:5]):  # Печатаем первые 5 строк
            print(f"Строка {i}: {row}")

        # Создаем DataFrame - берем все строки кроме заголовка
        # Используем только первые 5 столбцов (A-E)
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
        print("\nDataFrame перед обработкой:")
        print(df.head())

        # Преобразуем типы данных
        try:
            df['Дата'] = pd.to_datetime(df['Дата'], format='%Y-%m-%d', errors='coerce')
            df['Подходы'] = pd.to_numeric(df['Подходы'], errors='coerce')
            df['Повторения'] = pd.to_numeric(df['Повторения'], errors='coerce')
            df['Вес (кг)'] = pd.to_numeric(df['Вес (кг)'], errors='coerce')

            # Удаляем строки с некорректными данными
            df = df.dropna(subset=['Дата', 'Упражнение'])

            # Фильтруем аномальные значения веса
            df = df[(df['Вес (кг)'] >= 0) & (df['Вес (кг)'] < 1000)]

            print("\nDataFrame после обработки:")
            print(df.head())
        except Exception as e:
            await message.answer("Ошибка при обработке данных таблицы")
            print(f"Ошибка преобразования данных: {str(e)}")
            await state.clear()
            return

        if df.empty:
            await message.answer("Нет корректных данных для анализа")
            print("DataFrame пуст после обработки")
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

        # Создаем графики
        img_buffer = BytesIO()
        plt.figure(figsize=(12, 16))

        # 1. Количество подходов по упражнениям
        plt.subplot(3, 1, 1)
        df_grouped = df.groupby('Упражнение')['Подходы'].sum()
        df_grouped.plot(kind='bar', color='skyblue')
        plt.title(f'Подходы по упражнениям {period_title}')
        plt.ylabel('Количество подходов')
        plt.grid(axis='y')

        # 2. Общее количество повторений
        plt.subplot(3, 1, 2)
        df['Общие_повторения'] = df['Подходы'] * df['Повторения']
        df_reps = df.groupby('Упражнение')['Общие_повторения'].sum()
        df_reps.plot(kind='bar', color='lightgreen')
        plt.title('Общее количество повторений')
        plt.ylabel('Количество повторений')
        plt.grid(axis='y')

        # 3. Активность по дням
        plt.subplot(3, 1, 3)
        df['Дата_группа'] = df['Дата'].dt.date
        daily_count = df['Дата_группа'].value_counts().sort_index()
        daily_count.plot(kind='bar', color='salmon')
        plt.title('Активность по дням')
        plt.ylabel('Количество записей')
        plt.xticks(rotation=45)
        plt.grid(axis='y')

        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=80)
        plt.close()

        # Формируем текстовую статистику
        total_reps = (df['Подходы'] * df['Повторения']).sum()
        most_common_exercise = df['Упражнение'].mode()[0] if not df['Упражнение'].mode().empty else "нет данных"
        most_active_day = df['Дата_группа'].value_counts().idxmax().strftime('%d.%m.%Y') if not df[
            'Дата_группа'].value_counts().empty else "нет данных"

        stats_text = (
            f"📊 Статистика {period_title}:\n"
            f"• Упражнений: {len(df['Упражнение'].unique())}\n"
            f"• Тренировок: {len(df)}\n"
            f"• Подходов: {int(df['Подходы'].sum())}\n"
            f"• Повторений: {int(total_reps)}\n"
            f"• Популярное упражнение: {most_common_exercise}\n"
            f"• Активный день: {most_active_day}\n"
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
        print(f"Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await state.clear()