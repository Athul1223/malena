import logging

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.DEBUG)

app = Client(
    "my_bot",
    api_id=12345,
    api_hash="abcdefghijklmnopqrstuvwxyz012345",
    session_name="my_bot_session"
)

series_data = {}

@app.on_message(filters.command(["series"]))
async def handle_command(client, message):
    query = message.text.split(" ", 1)[-1]
    if not query:
        await message.reply_text("Please enter a series name to search for.")
        return

    series_name = query.lower()
    if series_name not in series_data:
        await message.reply_text(f"No results found for {series_name}.")
        return

    series = series_data[series_name]
    if len(series["languages"]) > 1:
        language_buttons = [
            InlineKeyboardButton(lang, callback_data=f"lang_{lang}")
            for lang in series["languages"]
        ]
        language_markup = InlineKeyboardMarkup([language_buttons])
        await message.reply_text("Please choose a language:", reply_markup=language_markup)
        return
    else:
        language = series["languages"][0]

    if len(series["seasons"]) > 1:
        season_buttons = [
            InlineKeyboardButton(season, callback_data=f"season_{season}")
            for season in series["seasons"]
        ]
        season_markup = InlineKeyboardMarkup([season_buttons])
        await message.reply_text(f"Please choose a season for {language}:",
                                  reply_markup=season_markup)
        return
    else:
        season = series["seasons"][0]

    if len(series["qualities"]) > 1:
        quality_buttons = [
            InlineKeyboardButton(quality, callback_data=f"quality_{quality}")
            for quality in series["qualities"]
        ]
        quality_markup = InlineKeyboardMarkup([quality_buttons])
        await message.reply_text(f"Please choose a quality for {language} {season}:",
                                  reply_markup=quality_markup)
        return
    else:
        quality = series["qualities"][0]

    channel_id = series["channel_id"]
    await handle_channel_message(client, message, channel_id, series_name, language, season, quality)

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    data = callback_query.data.split("_")
    query_type = data[0]
    query_value = data[1]

    if query_type == "lang":
        series_name = callback_query.message.text.split("Please choose a language:")[0].strip()
        series = series_data[series_name.lower()]
        series["languages"] = [query_value]

        if len(series["seasons"]) > 1:
            season_buttons = [
                InlineKeyboardButton(season, callback_data=f"season_{season}")
                for season in series["seasons"]
            ]
            season_markup = InlineKeyboardMarkup([season_buttons])
            await callback_query.message.edit_text(f"Please choose a season for {query_value}:",
                                                    reply_markup=season_markup)
            await callback_query.answer()
            return
        else:
            season = series["seasons"][0]
            series["seasons"] = {season: series["seasons"][season]}
            quality_buttons = create_quality_buttons(series["seasons"][season], query_value)
            quality_markup = InlineKeyboardMarkup(quality_buttons)
            await callback_query.message.edit_text(f"Please choose a quality for {query_value} - {season}:",
                                                    reply_markup=quality_markup)
            await callback_query.answer()
            return

    elif query_type == "season":
        series_name = callback_query.message.text.split("Please choose a season for")[0].strip()
        series = series_data[series_name.lower()]
        season = query_value
        series["seasons"] = {season: series["seasons"][season]}
        quality_buttons = create_quality_buttons(series["seasons"][season], series["languages"][0])
        quality_markup = InlineKeyboardMarkup(quality_buttons)
        await callback_query.message.edit_text(f"Please choose a quality for {series['languages'][0]} - {season}:",
                                                reply_markup=quality_markup)
        await callback_query.answer()
        return

    elif query_type == "quality":
        series_name = callback_query.message.text.split("Please choose a quality for")[0].strip()
        series = series_data[series_name.lower()]
        season = list(series["seasons"].keys())[0]
        quality = query_value
        results = await search_files(series_name, season, quality, series["languages"][0])
        if len(results) == 0:
            await callback_query.message.edit_text("Sorry, no files found for the selected criteria.")
        else:
            for result in results:
                await client.send_document(callback_query.from_user.id, result)
        await callback_query.answer()
        return

    else:
        await callback_query.answer("Invalid query!")

app.run()
