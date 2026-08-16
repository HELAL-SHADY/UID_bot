from __future__ import annotations

import time
from collections import defaultdict
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.database import (
    add_submission,
    add_transaction,
    create_withdraw_request,
    ensure_user,
    get_leaderboard,
    get_stats_summary,
    get_user_by_telegram_id,
    get_user_stats,
    is_uid_submitted,
    refresh_ranks,
    set_balance,
)
from bot.config import ADMIN_ID, RATE_LIMIT_PER_MINUTE, REWARD_AMOUNT, REQUIRED_CHANNEL, REQUIRED_CHANNEL_URL
from bot.handlers.admin import notify_admin_of_submission, notify_admin_of_withdrawal
from bot.utils.logging import setup_logging

logger = setup_logging()
USER_ACTION_TIMES: dict[int, list[float]] = defaultdict(list)


def get_welcome_text(language: str = "en") -> str:
    return {
        "en": (
            "Welcome to the Bybit UID Review Bot!\n\n"
            "Here’s how the reward system works:\n"
            "• Submit your Bybit UID for review\n"
            f"• If approved, you receive a ${REWARD_AMOUNT:.2f} reward balance\n"
            "• You can track your balance, statistics, and leaderboard here\n\n"
            "To get started, use the buttons below."
        ),
        "ar": (
            "مرحبًا بك في بوت مراجعة Bybit UID!\n\n"
            "إليك كيف تعمل نظام المكافآت:\n"
            "• أرسل Bybit UID الخاص بك للمراجعة\n"
            f"• إذا تمت الموافقة عليه، ستحصل على رصيد مكافأة بقيمة {REWARD_AMOUNT:.2f}$ دولار\n"
            "• يمكنك متابعة رصيدك وإحصائياتك ولوحة المتصدرين هنا\n\n"
            "للبداية، استخدم الأزرار أدناه."
        ),
    }.get(language, "en")


def build_force_sub_keyboard() -> InlineKeyboardMarkup:
    channel_link = REQUIRED_CHANNEL_URL
    if not channel_link and REQUIRED_CHANNEL:
        clean_channel = REQUIRED_CHANNEL.lstrip("@")
        channel_link = f"https://t.me/{clean_channel}"

    keyboard = []
    if channel_link:
        keyboard.append([InlineKeyboardButton("📢 الاشتراك في القناة / Join Channel", url=channel_link)])
    keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك / Check Subscription", callback_data="check_subscription")])
    return InlineKeyboardMarkup(keyboard)


def get_force_sub_text(language: str = "ar") -> str:
    return {
        "en": (
            "⚠️ Subscription Required\n\n"
            "You must subscribe to our Telegram channel first to use this bot.\n"
            "Please click the channel link below to join, then press 'Check Subscription'."
        ),
        "ar": (
            "⚠️ اشترك في القناة أولاً\n\n"
            "عذراً، يجب عليك الاشتراك في القناة الرسمية لاستخدام البوت.\n"
            "اشترك في القناة من الزر أدناه ثم اضغط على \"تحقق من الاشتراك\"."
        ),
    }.get(language, "ar")


async def check_channel_subscription(bot, user_id: int) -> bool:
    if not REQUIRED_CHANNEL or REQUIRED_CHANNEL == "@YourChannelUsername":
        return True
    if user_id == ADMIN_ID:
        return True
    try:
        chat_id = REQUIRED_CHANNEL
        if not (chat_id.startswith("@") or chat_id.startswith("-")):
            chat_id = f"@{chat_id}"
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["creator", "administrator", "member", "restricted"]
    except Exception as exc:
        logger.warning("Error checking channel subscription for user %s: %s", user_id, exc)
        return True


def get_user_language(user) -> str:
    if not user:
        return "en"
    return user.get("language", "en") if isinstance(user, dict) else "en"


def check_rate_limit(user_id: int) -> bool:
    now = time.time()
    timestamps = [ts for ts in USER_ACTION_TIMES[user_id] if now - ts < 60]
    timestamps.append(now)
    USER_ACTION_TIMES[user_id] = timestamps
    return len(timestamps) <= RATE_LIMIT_PER_MINUTE


def build_main_menu(language: str = "en") -> InlineKeyboardMarkup:
    labels = {
        "en": {
            "submit": "Submit UID",
            "balance": "My Balance",
            "withdraw": "Withdraw Balance",
            "stats": "My Statistics",
        },
        "ar": {
            "submit": "إرسال UID",
            "balance": "رصيدي",
            "withdraw": "سحب الرصيد",
            "stats": "إحصائياتي",
        },
    }
    current = labels.get(language, labels["en"])
    keyboard = [
        [InlineKeyboardButton(current["submit"], callback_data="submit_uid")],
        [InlineKeyboardButton(current["balance"], callback_data="my_balance")],
        [InlineKeyboardButton(current["withdraw"], callback_data="withdraw_balance")],
        [InlineKeyboardButton(current["stats"], callback_data="my_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_back_button(language: str = "en") -> InlineKeyboardMarkup:
    label = "🏠 القائمة الرئيسية / Main Menu" if language == "ar" else "🏠 Main Menu"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="main_menu")]])


def clear_user_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.chat_data is not None:
        context.chat_data.pop("state", None)
    if context.user_data is not None:
        context.user_data.pop("state", None)


def set_user_state(context: ContextTypes.DEFAULT_TYPE, state_name: str) -> None:
    if context.chat_data is not None:
        context.chat_data["state"] = state_name
    if context.user_data is not None:
        context.user_data["state"] = state_name


def get_user_state(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    state = None
    if context.user_data is not None:
        state = context.user_data.get("state")
    if not state and context.chat_data is not None:
        state = context.chat_data.get("state")
    return state


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return

    clear_user_state(context)

    user = update.effective_user
    ensure_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        full_name=(user.first_name or "") + (" " + user.last_name if user.last_name else ""),
    )

    user_record = get_user_by_telegram_id(user.id)
    language = get_user_language(user_record)

    subscribed = await check_channel_subscription(context.bot, user.id)
    if not subscribed:
        await update.message.reply_text(
            get_force_sub_text(language),
            reply_markup=build_force_sub_keyboard(),
        )
        return

    await update.message.reply_text(get_welcome_text(language), reply_markup=build_main_menu(language))


async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    if not check_rate_limit(query.from_user.id):
        await query.answer("Too many requests. Please slow down.", show_alert=True)
        return
    await query.answer()

    user = get_user_by_telegram_id(query.from_user.id)
    language = get_user_language(user)

    data = query.data or ""
    if data == "main_menu":
        clear_user_state(context)
        await query.edit_message_text(
            get_welcome_text(language),
            reply_markup=build_main_menu(language),
        )
        return

    if data == "check_subscription":
        subscribed = await check_channel_subscription(context.bot, query.from_user.id)
        if subscribed:
            await query.edit_message_text(
                get_welcome_text(language),
                reply_markup=build_main_menu(language),
            )
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    subscribed = await check_channel_subscription(context.bot, query.from_user.id)
    if not subscribed:
        await query.edit_message_text(
            get_force_sub_text(language),
            reply_markup=build_force_sub_keyboard(),
        )
        return

    if data == "submit_uid":
        prompt = {
            "en": "Please send your Bybit UID. It must be numeric and unique.",
            "ar": "يرجى إرسال Bybit UID الخاص بك. يجب أن يكون رقميًا وفريدًا.",
        }.get(language, "en")
        await query.edit_message_text(prompt, reply_markup=build_back_button(language))
        set_user_state(context, "awaiting_uid")
        return

    if data == "my_balance":
        clear_user_state(context)
        user = get_user_by_telegram_id(query.from_user.id)
        if not user:
            await query.edit_message_text("You are not registered yet. Start the bot again with /start.")
            return
        stats = get_user_stats(int(user["id"]))
        refresh_ranks()
        text = {
            "en": f"Your current balance is ${stats['balance']:.2f}\nApproved UIDs: {stats['approved_count']}\nTotal earnings: ${stats['total_earnings']:.2f}",
            "ar": f"رصيدك الحالي هو ${stats['balance']:.2f}\nUIDs المعتمدة: {stats['approved_count']}\nالإجمالي المكتسب: ${stats['total_earnings']:.2f}",
        }.get(language, "en")
        await query.edit_message_text(text, reply_markup=build_back_button(language))
        return

    if data == "withdraw_balance":
        user = get_user_by_telegram_id(query.from_user.id)
        if not user:
            await query.edit_message_text("You are not registered yet. Start the bot again with /start.")
            return
        stats = get_user_stats(int(user["id"]))
        text = {
            "en": f"Your current balance is ${stats['balance']:.2f}.\nPlease send your Binance UID and any withdrawal notes.\nExample: 12345678 | BTC network",
            "ar": f"رصيدك الحالي هو ${stats['balance']:.2f}.\nيرجى إرسال Binance UID الخاص بك وأي ملاحظات للسحب.\nمثال: 12345678 | BTC network",
        }.get(language, "en")
        await query.edit_message_text(text, reply_markup=build_back_button(language))
        set_user_state(context, "awaiting_withdrawal")
        return

    if data == "my_stats":
        clear_user_state(context)
        user = get_user_by_telegram_id(query.from_user.id)
        if not user:
            await query.edit_message_text("You are not registered yet. Start the bot again with /start.")
            return
        stats = get_user_stats(int(user["id"]))
        refresh_ranks()
        leaderboard = get_leaderboard()
        top_entries = []
        for index, row in enumerate(leaderboard[:5], start=1):
            name = row["full_name"] or row["username"] or f"User {row['telegram_id']}"
            top_entries.append(
                f"{index}. {name} — Approved: {row['approved_count']}, Earnings: ${float(row['total_earnings']):.2f}"
            )
        rank_text = "\n".join(top_entries) if top_entries else ("No leaderboard entries yet." if language == "en" else "لا توجد إدخالات في لوحة المتصدرين بعد.")
        text = {
            "en": f"Your rank: #{int(user['rank']) if user['rank'] else 'N/A'}\nApproved UIDs: {stats['approved_count']}\nTotal earnings: ${stats['total_earnings']:.2f}\n\nTop users:\n{rank_text}",
            "ar": f"رتبتك: #{int(user['rank']) if user['rank'] else 'N/A'}\nUIDs المعتمدة: {stats['approved_count']}\nالإجمالي المكتسب: ${stats['total_earnings']:.2f}\n\nأعلى المستخدمين:\n{rank_text}",
        }.get(language, "en")
        await query.edit_message_text(text, reply_markup=build_back_button(language))
        return


def is_valid_uid(value: str) -> bool:
    return value.isdigit() and 4 <= len(value) <= 20


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("Too many requests. Please wait a moment and try again.")
        return

    subscribed = await check_channel_subscription(context.bot, update.effective_user.id)
    if not subscribed:
        user = get_user_by_telegram_id(update.effective_user.id)
        language = get_user_language(user)
        await update.message.reply_text(
            get_force_sub_text(language),
            reply_markup=build_force_sub_keyboard(),
        )
        return

    state = get_user_state(context)
    text = (update.message.text or "").strip()

    if state == "awaiting_uid" or (not state and is_valid_uid(text)):
        await process_uid_submission(update, context)
        return

    if state == "awaiting_withdrawal":
        await process_withdrawal_request(update, context)
        return

    # Fallback for unhandled text messages
    user = get_user_by_telegram_id(update.effective_user.id)
    language = get_user_language(user)
    msg = {
        "en": "Please select an option from the main menu below:",
        "ar": "يرجى اختيار أحد الخيارات من القائمة الرئيسية أدناه:",
    }.get(language, "en")
    await update.message.reply_text(msg, reply_markup=build_main_menu(language))


async def process_uid_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_record = get_user_by_telegram_id(update.effective_user.id)
        language = get_user_language(user_record)
        uid = (update.message.text or "").strip()

        if not is_valid_uid(uid):
            msg = {
                "en": "Please enter a valid numeric Bybit UID.",
                "ar": "يرجى إدخال Bybit UID رقمي صحيح.",
            }.get(language, "en")
            await update.message.reply_text(msg)
            return

        user = ensure_user(
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name or "",
            last_name=update.effective_user.last_name or "",
            full_name=(update.effective_user.first_name or "") + (" " + update.effective_user.last_name if update.effective_user.last_name else ""),
        )

        existing_user = get_user_by_telegram_id(update.effective_user.id)
        if not existing_user:
            msg = {
                "en": "Your account could not be registered. Please try again.",
                "ar": "تعذر تسجيل حسابك. يرجى المحاولة مرة أخرى.",
            }.get(language, "en")
            await update.message.reply_text(msg, reply_markup=build_main_menu(language))
            return

        if is_uid_submitted(uid):
            msg = {
                "en": "⚠️ This UID has already been submitted before.",
                "ar": "⚠️ تم تقديم هذا الـ UID من قبل.",
            }.get(language, "en")
            await update.message.reply_text(msg, reply_markup=build_main_menu(language))
            clear_user_state(context)
            return

        submission_id = add_submission(int(existing_user["id"]), uid)
        msg = {
            "en": "✅ Your UID has been submitted successfully and is pending review.",
            "ar": "✅ تم إرسال الـ UID الخاص بك بنجاح وهو قيد المراجعة.",
        }.get(language, "en")
        await update.message.reply_text(msg, reply_markup=build_main_menu(language))

        try:
            await notify_admin_of_submission(update, context, submission_id, uid)
        except Exception as exc:
            logger.error("Failed to notify admin of submission %s: %s", submission_id, exc)

        clear_user_state(context)
    except Exception as exc:
        logger.error("Error processing UID submission: %s", exc, exc_info=True)
        clear_user_state(context)
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again with /start.",
            reply_markup=build_main_menu(),
        )


async def process_withdrawal_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_record = get_user_by_telegram_id(update.effective_user.id)
        language = get_user_language(user_record)
        payload = (update.message.text or "").strip()

        if not payload:
            msg = {
                "en": "Please provide a valid Binance UID and optional notes.",
                "ar": "يرجى تقديم Binance UID صحيح وملاحظات اختيارية.",
            }.get(language, "en")
            await update.message.reply_text(msg)
            return

        parts = [part.strip() for part in payload.split("|", 1)]
        binance_uid = parts[0]
        notes = parts[1] if len(parts) > 1 else "No additional notes"
        if not binance_uid or len(binance_uid) < 2:
            msg = {
                "en": "Please provide a valid Binance UID.",
                "ar": "يرجى تقديم Binance UID صحيح.",
            }.get(language, "en")
            await update.message.reply_text(msg)
            return

        user = get_user_by_telegram_id(update.effective_user.id)
        if not user:
            msg = {
                "en": "You are not registered yet.",
                "ar": "أنت غير مسجل بعد.",
            }.get(language, "en")
            await update.message.reply_text(msg)
            return

        stats = get_user_stats(int(user["id"]))
        if stats["balance"] <= 0:
            msg = {
                "en": "Your balance is zero, so there is nothing to withdraw.",
                "ar": "رصيدك صفر، لا يوجد شيء للسحب.",
            }.get(language, "en")
            await update.message.reply_text(msg, reply_markup=build_main_menu(language))
            clear_user_state(context)
            return

        withdrawal_info = f"Binance UID: {binance_uid}"
        if notes and notes != "No additional notes":
            withdrawal_info += f" | Notes: {notes}"

        request_id = create_withdraw_request(int(user["id"]), float(stats["balance"]), withdrawal_info)
        msg = {
            "en": "✅ Your withdrawal request has been submitted for review.",
            "ar": "✅ تم إرسال طلب السحب الخاص بك للمراجعة.",
        }.get(language, "en")
        await update.message.reply_text(msg, reply_markup=build_main_menu(language))

        try:
            await notify_admin_of_withdrawal(update, context, request_id, float(stats["balance"]), withdrawal_info)
        except Exception as exc:
            logger.error("Failed to notify admin of withdrawal %s: %s", request_id, exc)

        clear_user_state(context)
    except Exception as exc:
        logger.error("Error processing withdrawal request: %s", exc, exc_info=True)
        clear_user_state(context)
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again with /start.",
            reply_markup=build_main_menu(),
        )
